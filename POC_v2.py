__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import json
import requests
import preparation_aula
import treatments
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores.chroma import Chroma
from langchain.chains import SequentialChain
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain.chains import ConversationChain
from langchain.memory import ConversationSummaryBufferMemory
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
import os

#Setup 
load_dotenv()
llm = AzureChatOpenAI(
  openai_api_version = os.environ["AZURE_OPENAI_API_VERSION"],
  azure_deployment = os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"]
)

embeddings = AzureOpenAIEmbeddings(
    azure_endpoint='https://openai-dados-lab-poc.openai.azure.com/',
    api_key=os.environ["AZURE_OPENAI_API_KEY"]
)   
payload={}
headers = {
  'Accept': 'application/json',
  'x-secret': os.environ["ALEXANDRIA_SECRET"]
}

#rag
def get_aula_rag(learningUnit, questao):
    
    url_conteudo = f"https://cms-api-kroton.platosedu.io/api/v1/external/learning-units/{learningUnit}"
    aula = requests.request("GET", url_conteudo, headers=headers, data=payload)
    aula=preparation_aula.orquestrador(json.loads(aula.text))
    aula = treatments.treat_conteudo(aula)
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=400,
        length_function=len,
        is_separator_regex=False
        )

    conteudo=''
    for i in aula['sessao']:
        if i!='materia_id':
            conteudo=conteudo+aula[aula['sessao']==i]['conteudo'].item()
            
    docs = splitter.create_documents([conteudo])
    db = Chroma.from_documents(docs, embeddings)
    retriever = db.as_retriever()
    best_docs=retriever.get_relevant_documents(questao, search_kwargs={"k": 2})
    best_docs = "".join([best_docs[i].page_content for i in range(len(best_docs))])
        
    return best_docs

# funções de interação
def interacao_inicial(user_name, user_curso):
    template_inicial = \
    f"""Contexto: Atue como um tutor universitário que está ajudando o seu aluno de {user_curso}, chamado de {user_name} a responder um questionário.
    Ação: Parabenize seu aluno {user_name} pela conclusão de mais uma unidade de ensino, e que ele está mais próximo de se tornar um {user_curso}.
    Depois informe que você é um tutor que o ajudará a responder as questões.
    Atenção: Seja breve, amigável e não passe de um parágrafo."""
    completion_inicial = llm.invoke(template_inicial)
    completion_inicial = completion_inicial.content
    completion_inicial = completion_inicial.replace('Tutor: ','')
    return completion_inicial

def estrutura_bloom(questao, gabarito, feedback):
    
    first_prompt = ChatPromptTemplate.from_template(
        f"""
        Contexto: Atue como um professor universitário que possui uma habilidade incrível em dividir uma questão de prova em três tópicos.
        O primeiro tópico aborda conceitos básicos da questão. O segundo tópico relaciona os conceitos do tópico 1 com a questão.
        E o tópico 3 explica como desenvolver o raciocínio para chegar a resolução, sem revelar a resposta final.
        Ação: Divida em três tópicos a seguinte questão: {questao}. Sem revelar a resposta final.
        Utilize o seguinte texto para a sua resposta: {feedback}.
        Atenção: A IA é proibida de revelar a resposta final da questão, que é: {gabarito}. 
        """
        )
    chain_one = LLMChain(llm=llm, prompt=first_prompt, output_key="topicos_bloom")
    
    second_prompt = ChatPromptTemplate.from_template(
        """O texto a seguir possui três tópicos, extraia o título de cada um deles: {topicos_bloom}."""
        )
    chain_two = LLMChain(llm=llm, prompt=second_prompt, output_key="titulos_topicos")  
        
    third_prompt = ChatPromptTemplate.from_template(
        """Contexto: Para ajudar um aluno a compreender a resolução de uma questão, você a dividiu nos três tópicos
        a seguir: {titulos_topicos}.
        Ação: Diga de forma breve e direta que leu a questão e porque a dividiu em três tópicos. Depois explique os 
        três tópicos de forma breve e objetiva.
        System: Do not tell who you are in the completion neither introduce yourself """
        )
    chain_three = LLMChain(llm=llm, prompt=third_prompt, output_key="resposta_bloom")        
        
    overall_chain = SequentialChain(
        chains=[chain_one, chain_two, chain_three],
        input_variables=['questao'],
        output_variables=["topicos_bloom","titulos_topicos", "resposta_bloom"],
        verbose=False
        )
    resposta_topicos=overall_chain(questao)
    memory = ConversationSummaryBufferMemory(llm=llm, max_token_limit=2000)
    memory.save_context({"input": f"{resposta_topicos['topicos_bloom']}"}, {"output": f"{resposta_topicos['resposta_bloom']}"})
    conversation = ConversationChain(llm=llm, memory = memory, verbose=True)
    return resposta_topicos, conversation

def conversa(gabarito, resposta_topicos, conteudo_relacionado, conversation, resposta_aluno, user_name):
    
    prompt_conversa = ChatPromptTemplate.from_template(
        #Contexto: Tópicos de resolução: {topicos}.
        """Contexto: Atue como um professor universitário que dividiu uma questão em três tópicos, para que o seu aluno {user_name}
        consiga desenvolver a resolução da questão utilizando o seguinte texto: {conteudo_relacionado}.
        Ação: Responda a brevemente a pergunta: {resposta_aluno}.
        Ação: Se a pergunta não for específica responda: {resposta_topicos}.  
        Atenção: A resposta correta final nunca deverá ser revelada. Ao contrário, a IA deverá mostrar ao aluno como
        desenvolver o racionício para responder a questão.
        """
        )    
    formated_input = prompt_conversa.format_messages(
                    gabarito =gabarito,
                    resposta_topicos=resposta_topicos,
                    resposta_aluno = resposta_aluno,
                    conteudo_relacionado = conteudo_relacionado,
                    user_name = user_name            
                    )
    completion=conversation.predict(input=formated_input)
    conversation.memory.save_context({"input": f"{resposta_aluno}"}, {"output": f"{completion}"})
    return completion

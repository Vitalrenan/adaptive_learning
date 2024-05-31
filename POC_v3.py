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
  azure_deployment = os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
  temperature=0
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

def chat_memory(questao, conteudo_relacionado):
    #memory = ConversationSummaryBufferMemory(llm=llm, max_token_limit=2000)
    messages=[
        {"role": "system", "content":f"""Act as a very skilled university professor in assisting students on academic quizes.
        You often tell the necessary basic concepts to solve it and then ask if the student understood them or if wants to proceed to the resolution.
        The AI is assisting the student on this question: {questao}.
        The AI completion must use the following text as reference: {conteudo_relacionado}.
        Important: You must answer this onging conversation in brazillian portuguese, very briefly, concise and kindly."""}
        ]
    return messages


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
    f"""Context: Act as a kind academic professor assisting your student {user_name}, from {user_curso} course.
    Action: Cangratulate {user_name} for another step in {user_curso} carreer. Then just inform that you can help with
    the quiz question.
    Important: Answer briefly, concise and kindly in brazillian portuguese. Do not write more than one paragraph."""
    completion_inicial = llm.invoke(template_inicial)
    completion_inicial = completion_inicial.content
    completion_inicial = completion_inicial.replace('Tutor: ','')
    return completion_inicial

def conversa(input_aluno, messages):   
    input_aluno = f"""{input_aluno}. Atention! Do not solve the question. Instead of solving it,
    please explain me the necessary reasoning to solve it. Then, tell me to try to apply the reasoning.
    Do never offer to calculate too, tell me to try instead.
    System: Take into considerarion the previous conversation avoiding repetitiveness"""
    messages.append({"role": "user", "content": input_aluno})
    response=llm.invoke(messages)
    response = response.content
    if response.startswith('Olá!'):
        response = response.replace('Olá! ','')
    messages.append({"role": "assistant", "content": response})
    return response, messages




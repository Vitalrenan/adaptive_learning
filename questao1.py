import streamlit as st
import pickle
import json
import requests
import preparation_teste
import preparation_aula
import treatments
from POC_v3 import get_aula_rag,  interacao_inicial, conversa, chat_memory
from dotenv import load_dotenv
import os
import sqlite3

#Setup 
load_dotenv()
st.set_page_config(layout="wide")

def update_history():   
    conversation = st_messages
    with open('conversation.pickle', 'wb') as handle:
        pickle.dump(conversation, handle)

@st.cache_data      
def carregando_quiz(url_quiz,num_questao):
    payload={}
    headers = {'Accept': 'application/json', 'x-secret': os.environ["ALEXANDRIA_SECRET"] }
    if url_quiz:
        pass
    else:
        token='c43265d4-22e5-45d1-be50-cd3a8ce50b2c'
        url_quiz = f"https://cms-api-kroton.platosedu.io/api/v1/external/questions?learningUnits[]={token}&bankType=endOfUnit&quantity=5"
    quiz = requests.request("GET", url_quiz, headers=headers, data=payload)
    quiz=preparation_teste.read_teste(json.loads(quiz.text))
    learningUnit=quiz[0]['learningUnit']
    quiz = treatments.treat_quiz(quiz)

    url_conteudo = f"https://cms-api-kroton.platosedu.io/api/v1/external/learning-units/{learningUnit}"
    aula = requests.request("GET", url_conteudo, headers=headers, data=payload)
    aula=preparation_aula.orquestrador(json.loads(aula.text))
    aula = treatments.treat_conteudo(aula)
    questao = quiz[quiz['num_questao']==num_questao]['questao'].item() 
    alternas = quiz[quiz['num_questao']==num_questao]['alternativas'].item().split("',")
    alternas = [i.replace('[','').replace(']','').replace("'",'').replace(",",'').replace(r"\xa0",'') for i in alternas]
    conteudo_relacionado=get_aula_rag(learningUnit=learningUnit, questao=questao)    
    return quiz, num_questao, questao, alternas, conteudo_relacionado
    

#read previous conversation
def load_previous_messages():
    try:
        with open('conversation.pickle', 'rb') as conversation_pkl:
            st_messages = pickle.load(conversation_pkl)
    except:
        st_messages = []
    ai_messages = chat_memory(questao, conteudo_relacionado)
    return ai_messages, st_messages

#Title
st.title("Feedback personalizado de compreensão de conteúdo")

#Sidebar
with st.sidebar:
    user_name = st.text_input('Insira seu nome:')
    user_curso = st.selectbox("Curso", ("Engenharia Elétrica", 'Administração','Licenciatura','Psicologia'))
    
#Page rendering
col1, col2 = st.columns(spec=[0.6,0.4])

#Renderiza Quiz
with col1: 
    url_quiz = st.text_input('Insira a URL do quiz alexandria')  
    quiz, num_questao, questao, alternas, conteudo_relacionado = carregando_quiz(url_quiz,1)
    st.markdown(f'Questão {num_questao}: {questao}')
    sub_col1, sub_col2 = st.columns(spec=[0.7,0.4])
    with sub_col1:
        st.radio('Alternativas',options=alternas)
    with sub_col2:
        feedback=quiz[quiz['num_questao']==num_questao]['feedback'].item()
        gabarito=quiz[quiz['num_questao']==num_questao]['gabarito'].item()
        st.markdown(f"Gabarito: {feedback}")

if st.button("questão 2"):
    st.switch_page("pages/questao2.py") 
 
#Renderiza Chat   
with col2:
    
    #Monta interações iniciais ou recupera histórico
    reset_chat = st.button('Resetar histórico',use_container_width=True)
    ai_messages, st_messages = load_previous_messages()
    if st_messages == []:      
        first_interaction = interacao_inicial(user_name, user_curso) 
        #response, ai_messages = interacao_secundaria(first_interaction, ai_messages)     
        st_messages.append({"role": "assistant", "content": first_interaction})
        #st_messages.append({"role": "assistant", "content": response.content})
    elif reset_chat:
        st_messages = []
        first_interaction = interacao_inicial(user_name, user_curso) 
        #response, ai_messages = interacao_secundaria(first_interaction, ai_messages)     
        st_messages.append({"role": "assistant", "content": first_interaction})
        #st_messages.append({"role": "assistant", "content": response.content})
        update_history()
    else:
        pass
        
    #Renderiza chat                
    for n,message in enumerate(st_messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])      
                  
    #Monta interação de chat pós introdução
    if resposta_aluno := st.chat_input("Responda aqui"):
        st_messages.append({"role": "user", "content": f"{resposta_aluno}"})
        #completion, messages, validator, original_response = conversa(resposta_aluno, ai_messages)
        completion, messages = conversa(resposta_aluno, ai_messages)
        #if validator=='True':
        #    print(str('#'*100),'\nOriginal:',original_response)
        st_messages.append({"role": "assistant", "content": f"{completion}"})
        update_history()
        st.rerun()

update_history()
   

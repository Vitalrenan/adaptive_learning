import streamlit as st
import pickle
import json
import requests
import preparation_teste
import preparation_aula
import treatments
from POC_v2 import get_aula_rag, interacao_inicial, estrutura_bloom, conversa


st.set_page_config(layout="wide")
st.title("Feedback personalizado de compreensão de conteúdo")

#caching on browser
@st.cache_data
def update_history():   
    conversation = st.session_state.messages
    with open('conversation.pickle', 'wb') as handle:
        pickle.dump(conversation, handle)
  
@st.cache_data      
def carregando_quiz(url_quiz,num_questao):
    payload={}
    headers = {'Accept': 'application/json', 'x-secret': '148baeda-e1f2-11ec-8fea-0242ac120002' }
    if url_quiz:
        print('if')
        pass
    else:
        print('else')
        url_quiz='https://cms-api-kroton.platosedu.io/api/v1/external/questions?learningUnits[]=c43265d4-22e5-45d1-be50-cd3a8ce50b2c&bankType=endOfUnit&quantity=5'
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
try:
    with open('conversation.pickle', 'rb') as conversation_pkl:
        conversation = pickle.load(conversation_pkl)
except:
    conversation=[]

#Quiz setup
col1, col2 = st.columns(spec=[0.6,0.4])
with col1: 
    
    url_quiz = st.text_input('Insira a URL do quiz alexandria')
    try:    
        quiz, num_questao, questao, alternas, conteudo_relacionado = carregando_quiz(url_quiz,4)
        print(questao)
        st.markdown(f'Questão {num_questao}: {questao}')
        sub_col1, sub_col2 = st.columns(spec=[0.7,0.4])
        with sub_col1:
            st.radio('Alternativas',options=alternas)
        with sub_col2:
            feedback=quiz[quiz['num_questao']==num_questao]['feedback'].item()
            gabarito=quiz[quiz['num_questao']==num_questao]['gabarito'].item()
            st.markdown(f"Gabarito: {feedback}")
    except:
        pass

if st.button("questão 5"):
    st.switch_page("pages/questao5.py") 
    
with col2:
    reset_chat = st.button('Resetar histórico',use_container_width=True)   
    if conversation == []:
        st.session_state.messages = []
        first_interaction = interacao_inicial()
        st.session_state.messages.append({"role": "assistant", "content": first_interaction})
    elif reset_chat:
        st.session_state.messages = []
        first_interaction = interacao_inicial()
        st.session_state.messages.append({"role": "assistant", "content": first_interaction})
    else:
        st.session_state.messages=conversation
                
    for n,message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
    if resposta_aluno := st.chat_input("Responda aqui"):
        st.session_state.messages.append({"role": "user", "content": resposta_aluno})

        topicos_bloom, conversation = estrutura_bloom(questao, gabarito, feedback)
        completion = conversa(topicos_bloom['topicos_bloom'], topicos_bloom['resposta_bloom'], conteudo_relacionado, conversation, resposta_aluno)
        #print(topicos_bloom['resposta_bloom'])
        st.session_state.messages.append({"role": "assistant", "content": f"{completion}"})
        update_history()
        st.rerun()



        
update_history()
   

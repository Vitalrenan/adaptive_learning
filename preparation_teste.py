import json
from bs4 import BeautifulSoup

def read_teste(data):
    teste={}
    for num_questao in range(len(data)):
        aux = {
            'baseText':get_text_from_item(data[num_questao],'baseText'),
            'statement':get_text_from_item(data[num_questao],'statement'),
            'learningUnit':get_text_from_item(data[num_questao],'learningUnit'),
            'feedback':get_text_from_item(data[num_questao],'feedback'),
            'choices':get_text_choices(data[num_questao],'choices'),
        }
        teste[num_questao]=aux
    return teste
        
        

def get_text_from_item(data,item):
    soup = BeautifulSoup(data[item], 'html.parser')
    text_content = ''.join([p.get_text() for p in soup.find_all('p')])
    if text_content=='':
        return soup
    else:
        conteudo = str(text_content)
        return conteudo
        
def get_text_choices(data,item):
    lista_alternativas=[]
    for alternativa in data[item]:
        soup = BeautifulSoup(alternativa['description'], 'html.parser')        
        text_content = ''.join([p.get_text() for p in soup.find_all('p')])
        conteudo = str(text_content)
        lista_alternativas.append(conteudo)
        if alternativa['is_correct']==True:
            alt_correta=conteudo       
    return lista_alternativas, alt_correta

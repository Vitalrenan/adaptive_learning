import json
from bs4 import BeautifulSoup

#DEFINIÇÃO DE FUNÇÕES DE RASPAGEM
def get_objvideo_to_text(objeto_de_aula):
    text_content=''
    dict_obj_aula={}
    dict_obj_aula['titulo']=objeto_de_aula['title'].upper()
    aux={}
    for asset in objeto_de_aula['assets']:
        if asset['type']=='VIDEO':
            aux['link_video']=asset['videoLink']
        if asset['type']=='TEXT':
            soup = BeautifulSoup(asset['content'], 'html.parser')
            text_content = ''.join([p.get_text() for p in soup.find_all('p')])
            aux['descricao']=text_content
    dict_obj_aula['conteudo']=aux
    return dict_obj_aula
        
def get_obj_to_text(objeto_de_aula):
    text_content=''
    dict_obj_aula={}
    dict_obj_aula['tipo']=objeto_de_aula['type'].upper()
    dict_obj_aula['titulo_obj']=objeto_de_aula['title'].upper()
    lista_aux=[]
    for asset in objeto_de_aula['assets']:
        aux={}
        if asset['type']=='TEXT':
            soup = BeautifulSoup(asset["content"], 'html.parser')
            text_content = ''.join([p.get_text() for p in soup.find_all('p')])
            if text_content!='':
                aux['texto']=text_content
        if asset['type']=='IMAGE':
            aux['img_link']=asset['image']['baseUrl']            
        if asset['type']=='FORMULA':
            aux['equacao']=asset['content']
        lista_aux.append(aux)
    dict_obj_aula['conteudo']=lista_aux
    return dict_obj_aula
            
def orquestrador(data):
    aula = {}
    aula['materia_id']=data['id']
    for sessao_de_aula in data['sections']:
        aula['sessao_'+str(sessao_de_aula['order'])]={
            'titulo':sessao_de_aula['title']
        }
        
        for n,objeto_de_aula in enumerate(sessao_de_aula['learningObjects']):
            if objeto_de_aula['type']=='video':
                aula['sessao_'+str(sessao_de_aula['order'])]['video']=get_objvideo_to_text(objeto_de_aula)   
            if objeto_de_aula['type']!='video':
                aula['sessao_'+str(sessao_de_aula['order'])]['obj_estudo_'+str(n)]=get_obj_to_text(objeto_de_aula) 
    return aula     
    
                
#EXECUÇÃO

with open('request_aula.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

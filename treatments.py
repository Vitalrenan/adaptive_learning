import pandas as pd

def treat_conteudo(aula_exemplo):
    df=pd.DataFrame()
    aux={}
    for i in aula_exemplo.keys():
        texto_base=''
        aux['sessao']=i
        if i!='materia_id':
            for j in aula_exemplo[i]:
                if j=='titulo':
                    texto_base=texto_base+'titulo: '+str(aula_exemplo[i]['titulo']+' ')
                else:
                    if j!='video':
                        for k in aula_exemplo[i][j]:
                            if k=='titulo_obj':
                                texto_base=texto_base+str(aula_exemplo[i][j][k])+' '
                            elif k!='tipo':
                                for n in range(len(aula_exemplo[i][j][k])):
                                    for l in aula_exemplo[i][j][k][n]:
                                        if l=='texto':
                                            texto_base=texto_base+str(aula_exemplo[i][j][k][n][l])+' '
                                        elif l =='equacao':
                                            texto_base=texto_base+str(aula_exemplo[i][j][k][n][l])+' '
        aux['conteudo']=pd.Series(texto_base)
        df=pd.concat([df,pd.DataFrame(aux)])
        df.loc[df.sessao=='materia_id','conteudo']=aula_exemplo['materia_id']
    return df
    

def treat_quiz(teste_exemplo):
    df=pd.DataFrame()
    aux={}
    for i in range(0,len(teste_exemplo)):
        
        aux['num_questao']=i+1
        aux['questao']= pd.Series(
            str(teste_exemplo[i]['baseText'])\
            +str(teste_exemplo[i]['statement']))
        aux['alternativas']= pd.Series(
            str(teste_exemplo[i]['choices'][0]))        
        aux['gabarito']= pd.Series(
            str(teste_exemplo[i]['choices'][1]))     
        aux['feedback']=pd.Series(
            str(teste_exemplo[i]['feedback'])
        )
        df=pd.concat([df,pd.DataFrame(aux)])
    return df
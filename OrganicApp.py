import streamlit as st
import pandas as pd
import numpy as np
from pycaret.regression import load_model, predict_model
from PIL import Image
import locale
import datetime
import os
import base64
from io import BytesIO

# Imagem
img = Image. open('logo_app.png')
st.image(img)

# Funções

# Função para limpar df
def clean_df(df):
    
    # Renomeando colunas
    df.rename(columns={'Date':'Data','Visitantes da página "Detalhes do app": Todos os países / todas as regiões':'Visitas',
                  'Aquisições da página "Detalhes do app": Todos os países / todas as regiões':'T_instalacoes',
                  'Taxa de conversão da página "Detalhes do app": Todos os países / todas as regiões':'Conversao'}, inplace=True)
    
    # Alterando formato de datas
    locale.setlocale(locale.LC_ALL, 'pt_pt.UTF-8')
    df['Data'] = df['Data'].apply(lambda x: datetime.datetime.strptime(x, '%d de %b de %Y').strftime('%d/%m/%Y'))
    
    # Limpando Conversao e transformando em float
    df['Conversao'] = df['Conversao'].str.replace('%','')
    df['Conversao'] = df['Conversao'].str.replace(',','.')
    df['Conversao'] = df['Conversao'].astype('float64')
    
    # Limpando Visitas e Instalações e transformando em Int
    df['T_instalacoes'] = df['T_instalacoes'].str.replace('.','')
    df['T_instalacoes'] = df['T_instalacoes'].astype('float64')
    df['Visitas'] = df['Visitas'].str.replace('.','')
    df['Visitas'] = df['Visitas'].astype('float64')    

    return df

# Função para transformar df em excel
def to_excel(df):
	output = BytesIO()
	writer = pd.ExcelWriter(output, engine='xlsxwriter')
	df.to_excel(writer, sheet_name='Planilha1',index=False)
	writer.save()
	processed_data = output.getvalue()
	return processed_data
	
# Função para gerar link de download
def get_table_download_link(df):
	val = to_excel(df)
	b64 = base64.b64encode(val)
	return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="extract.xlsx">Download</a>'

st.title('Organic App')
st.write('''Esta aplicação tem como objetivo estimar os downloads orgânicos e não-orgânicos tendo como base o total de downloads
	do Google Console''')

st.subheader('Como utilizar')
st.write('''1 - Baixe os dados de instalações na aba de Análise de Conversão no Google Console
	\n 2 - Faça a extração do arquivo daily_performance.csv
	\n 3 - Insira a base de dados original (sem nenhuma modificação) no local indicado
	\n 4 - Selecione a Categoria, Perfil de Sales e fase do AIS pertinente do app carregado
	\n 5 - Clique em Predict para obter as estimativas''')

####### Upload dataset #######
#st.subheader('Dados')
data = st.file_uploader("Insira a base de dados", type='csv')
if data is not None:
	df = pd.read_csv(data, usecols=[0,1,2,3], dtype={1:"O",2:"O"})
	df_clean = clean_df(df)	
	st.write(df_clean.head(10))
	st.write('Mostrando as 10 primeiras linhas da base de dados')
	st.write('Esta visualização já possui um pré-processamento')


menu_categoria = ['Financas', 'Compras', 'Outro']
categoria = st.selectbox('Selecione a categoria do app', menu_categoria)

menu_perfil = ['A1','A2','B4','A4','BA4','BA2']
perfil= st.selectbox('Selecione o perfil de Sales', menu_perfil)

menu_ais = ['Appear', 'Improve', 'Scale']
ais = st.selectbox('Selecione a fase do AIS', menu_ais)

# Adicionando coluna de dia da semana
df_clean['Data'] = pd.to_datetime(df_clean['Data'], format='%d/%m/%Y')
df_clean['weekday'] = df_clean['Data'].dt.day_name()

# Adicionando outras colunas de predição
df_clean['Categoria'] = categoria
df_clean['Perfil'] = perfil
df_clean['AIS'] = ais

# Criando input df
input_df = df_clean[['Perfil', 'AIS', 'Categoria','T_instalacoes','weekday','Conversao']]

# Carregando modelo
model = load_model('organic_model_09032021')

# Predict Organic
st.write('Clique em Predict para fazer a estimativa dos downloads orgânicos')
if st.button('Predict'):
	output = predict_model(model, data = input_df)

	preds = output['Label']

	# Criando df para exportar
	df_final = df_clean[['Data', 'T_instalacoes', 'Visitas','Conversao']]
	df_final['Instalações Orgânicas (Estimado)'] = round(preds,0)
	
	df_final['Instalações Não-Orgânicas (Estimado)'] = df_final['T_instalacoes'] - df_final['Instalações Orgânicas (Estimado)']
	df_final['Data'] = df_final['Data'].dt.strftime('%d/%m/%Y')
	df_final.rename(columns={'T_instalacoes':'Total de Instalações', 'Conversao': 'Conversão(%)'}, inplace=True)

	st.write(df_final)
	st.write('Clique em Download para baixar o arquivo')
	st.markdown(get_table_download_link(df_final), unsafe_allow_html=True)
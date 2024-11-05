import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.linear_model import LinearRegression
from fpdf import FPDF
import datetime

# Função para gerar relatório em PDF
def gerar_relatorio_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Relatório de Vendas de Carros", ln=True, align='C')
    pdf.cell(200, 10, txt=f'Data: {datetime.datetime.now().strftime("%Y-%m-%d")}', ln=True)
    
    # Adiciona a tabela de vendas
    pdf.cell(200, 10, txt="Tabela de Vendas", ln=True)
    for index, row in data.iterrows():
        pdf.cell(200, 10, txt=f"{row['Marca']} | {row['Modelo']} | {row['Quantidade']} | {row['Preço Unitário']}", ln=True)
    
    pdf_file = "relatorio_vendas.pdf"
    pdf.output(pdf_file)
    return pdf_file

# Carregar os dados
df = pd.read_csv('Base\vendas_carros.csv')

# Definir usuários e senhas para o sistema de login
usuarios = {
    "admin": "admin123",
    "user": "user123"
}

# Configurar login
st.title('Sistema de Login')
if 'login' not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    username = st.text_input('Usuário')
    password = st.text_input('Senha', type='password')

    if st.button('Entrar'):
        if username in usuarios and usuarios[username] == password:
            st.session_state.login = True
            st.session_state.username = username
            st.success("Login bem-sucedido!")
        else:
            st.error("Usuário ou senha inválidos.")
else:
    st.success(f"Bem-vindo, {st.session_state.username}!")

    # Página inicial do dashboard
    st.sidebar.title('Navegação')
    pagina = st.sidebar.selectbox('Selecione uma Página', 
                                   ['Página Inicial', 
                                    'Relatório por Marca', 
                                    'Relatório por Categoria', 
                                    'Relatório por Região', 
                                    'Análise Preditiva', 
                                    'Gerar Relatório PDF'])

    # Página Inicial
    if pagina == 'Página Inicial':
        st.header('Visão Geral das Vendas de Carros')
        st.write("Este é um dashboard completo para análise de vendas de carros.")

    # Relatório por Marca
    elif pagina == 'Relatório por Marca':
        st.header('Relatório por Marca')
        marcas = df['Marca'].unique()
        marca_selecionada = st.selectbox('Selecione uma Marca', marcas)

        df_marca = df[df['Marca'] == marca_selecionada]
        vendas_totais = df_marca.groupby('Data da Venda')['Quantidade'].sum().reset_index()

        fig = px.line(vendas_totais, x='Data da Venda', y='Quantidade', 
                      title=f'Vendas ao Longo do Tempo - {marca_selecionada}')
        st.plotly_chart(fig)

    # Relatório por Categoria
    elif pagina == 'Relatório por Categoria':
        st.header('Relatório por Categoria')
        categorias = df['Categoria'].unique()
        categoria_selecionada = st.selectbox('Selecione uma Categoria', categorias)

        df_categoria = df[df['Categoria'] == categoria_selecionada]
        vendas_categoria = df_categoria.groupby('Marca')['Quantidade'].sum().reset_index()

        fig = px.bar(vendas_categoria, x='Marca', y='Quantidade', 
                      title='Vendas Totais por Marca na Categoria Selecionada')
        st.plotly_chart(fig)

    # Relatório por Região
    elif pagina == 'Relatório por Região':
        st.header('Relatório por Região')
        regioes = df['Região'].unique()
        regiao_selecionada = st.selectbox('Selecione uma Região', regioes)

        df_regiao = df[df['Região'] == regiao_selecionada]
        vendas_regiao = df_regiao.groupby('Marca')['Quantidade'].sum().reset_index()

        fig = px.bar(vendas_regiao, x='Marca', y='Quantidade', 
                      title='Vendas Totais por Marca na Região Selecionada')
        st.plotly_chart(fig)

    # Análise Preditiva
    elif pagina == 'Análise Preditiva':
        st.header('Análise Preditiva de Vendas')
        X = df[['Quantidade']]
        y = df['Preço Unitário']

        model = LinearRegression()
        model.fit(X, y)

        # Predição para vendas futuras
        predicoes = model.predict(X)

        df['Predições'] = predicoes
        fig = px.scatter(df, x='Quantidade', y='Predições', 
                         title='Predição de Preço Unitário Baseado na Quantidade Vendida')
        st.plotly_chart(fig)

    # Gerar Relatório PDF
    elif pagina == 'Gerar Relatório PDF':
        st.header('Gerar Relatório em PDF')
        if st.button('Gerar Relatório'):
            pdf_file = gerar_relatorio_pdf(df)
            st.success(f'Relatório gerado: {pdf_file}')
            st.download_button('Baixar Relatório', pdf_file, file_name='relatorio_vendas.pdf')

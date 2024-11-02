import streamlit as st
import pandas as pd  # Adicionada a importação do pandas
import plotly.express as px
import plotly.graph_objects as go

def pagina_analise(df_spn, df_iti):
    # Combine os dados e adicione uma coluna para identificar a aba de origem
    df_spn['Aba'] = 'SPN'
    df_iti['Aba'] = 'ITI'
    df_consolidado = pd.concat([df_spn, df_iti], ignore_index=True)

    # Filtros
    st.sidebar.header("Filtros por Área")
    setores_disponiveis = df_consolidado['Setor'].unique()
    setores_selecionados = [setor for setor in setores_disponiveis if st.sidebar.checkbox(setor, value=True)]
    df_filtrado = df_consolidado[df_consolidado['Setor'].isin(setores_selecionados)]

    st.title("Análise de Dados Consolidados - Backlog")
    st.write(f"**Total de Registros:** {len(df_filtrado)}")

    if not df_filtrado.empty:
        # (A lógica para criar os gráficos vai aqui)
        df_total_sector = df_filtrado['Setor'].value_counts()
        # Adicione mais lógica para gráficos e análises conforme necessário.

def pagina_sobre():
    st.title("Sobre este Aplicativo")
    st.write("Este aplicativo foi criado para ajudar na análise de dados consolidados.")
    st.write("Você pode filtrar os dados por setor e visualizar várias estatísticas.")
    st.write("Desenvolvedores: [Seu Nome]")  # Altere com seu nome

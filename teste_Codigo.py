import pandas as pd
import streamlit as st

@st.cache_data
def carregar_dados(caminho_arquivo):
    try:
        df_spn = pd.read_excel(caminho_arquivo, sheet_name='SPN', parse_dates=['Inicio_Semana', 'Final_Semana', 'Backlog', 'Data'])
        df_iti = pd.read_excel(caminho_arquivo, sheet_name='ITI', parse_dates=['Inicio_Semana', 'Final_Semana', 'Backlog', 'Data'])
        return df_spn, df_iti
    except FileNotFoundError:
        st.error("Arquivo não encontrado. Verifique o caminho e tente novamente.")
        return pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar os dados: {e}")
        return pd.DataFrame(), pd.DataFrame()

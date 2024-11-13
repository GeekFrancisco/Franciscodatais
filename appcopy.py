import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da página
st.set_page_config(page_title="DataPaws", page_icon="Base/IMG/Designer.jpeg", layout="wide")

# Carregar credenciais do .env
usuarios = {
    "emerson": (os.getenv("USERNAME_EMERSON"), "Emerson Simette"),
    "willian": (os.getenv("USERNAME_WILLIAN"), "Willian Jones Rios"),
    "rafael": (os.getenv("USERNAME_RAFAEL"), "Rafael Dall'Anese"),
    "admin": (os.getenv("USERNAME_ADMIN"), "Administrador"),
}

def verificar_login(username, password):
    """Verifica as credenciais do usuário."""
    if username in usuarios and password == usuarios[username][0]:
        return usuarios[username][1]  # Retorna o nome do usuário
    return None  # Retorna None se o login falhar

@st.cache_data
def carregar_dados(caminho_arquivo):
    """Carrega dados do arquivo Excel."""
    return pd.read_excel(caminho_arquivo, sheet_name=None)

# Caminho do arquivo Excel
caminho_arquivo = 'Base/consolidado.xlsx'

if 'login' not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    # Tela de Login
    st.markdown("""
    <style>
        .login {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background-color: #f7f7f7;
            font-family: 'Roboto', sans-serif;
        }
        .login h1 {
            color: #4CAF50;
            font-size: 3rem;
            margin-bottom: 20px;
        }
        .login form {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .login input {
            width: 100%;
            padding: 12px;
            margin: 8px 0;
            border-radius: 5px;
            border: 1px solid #ccc;
        }
        .login button {
            width: 100%;
            padding: 12px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 1.2rem;
        }
        .login button:hover {
            background-color: #45a049;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login">', unsafe_allow_html=True)
    st.markdown('<h1>DataPaws</h1>', unsafe_allow_html=True)

    with st.form(key='login_form', clear_on_submit=True):
        username = st.text_input("Usuário", placeholder="Username").lower()
        password = st.text_input("Senha", type="password", placeholder="Password")
        submit_button = st.form_submit_button("Entrar")
    
    if submit_button:
        nome_usuario = verificar_login(username, password)
        if nome_usuario:
            st.session_state.login = True
            st.session_state.nome_usuario = nome_usuario
            st.success("Login realizado com sucesso!")
        else:
            st.error("Usuário ou senha incorretos.")
    
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # Layout após o login
    st.markdown("""
    <style>
        .header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background-color: white;
            z-index: 2;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        .header h1 {
            font-size: 2rem;
            color: #4CAF50;
            margin: 0;
        }
        .sidebar {
            padding: 10px;
            background-color: #f4f4f4;
        }
        .sidebar button {
            background-color: #4CAF50;
            color: white;
            border-radius: 5px;
            width: 100%;
            padding: 10px;
            font-size: 1rem;
        }
        .sidebar button:hover {
            background-color: #45a049;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="header"><h1>DataPaws - Análise de Dados Consolidados</h1></div>', unsafe_allow_html=True)

    # Sidebar
    st.sidebar.header(f"Bem-vindo, {st.session_state.nome_usuario}")
    if st.sidebar.button("Logout"):
        st.session_state.login = False
        st.success("Logout realizado com sucesso!")

    # Carregar e processar os dados
    df_dados = carregar_dados(caminho_arquivo)
    df_spn = df_dados['SPN']
    df_iti = df_dados['ITI']

    if 'Setor' not in df_spn.columns or 'Setor' not in df_iti.columns:
        st.error("A coluna 'Setor' não foi encontrada em uma das abas. Verifique os nomes das colunas no arquivo.")
        st.stop()

    df_spn['Aba'] = 'SPN'
    df_iti['Aba'] = 'ITI'
    df_consolidado = pd.concat([df_spn, df_iti], ignore_index=True)

    # Barra lateral para filtros
    st.sidebar.header("Filtros")

    # Filtro de Setor
    setores_disponiveis = df_consolidado['Setor'].unique()
    setores_selecionados = st.sidebar.multiselect("Selecione os Setores", setores_disponiveis, default=setores_disponiveis)

    # Aplicar filtro ao DataFrame
    df_filtrado = df_consolidado[df_consolidado['Setor'].isin(setores_selecionados)]

    # Exibir totais
    total_registros = len(df_filtrado)
    total_resolvidos = len(df_filtrado[df_filtrado['Status'] == 'Resolvido'])
    total_pendentes = total_registros - total_resolvidos

    # Exibir totais e porcentagens
    percentual_resolvidos = (total_resolvidos / total_registros * 100) if total_registros > 0 else 0
    percentual_pendentes = (total_pendentes / total_registros * 100) if total_registros > 0 else 0

    st.write(f"**Total de Registros:** {total_registros} "
            f"**Resolvidos:** {total_resolvidos} ({percentual_resolvidos:.1f}%) "
            f"**Pendentes:** {total_pendentes} ({percentual_pendentes:.1f}%)")

    # Verificar se há dados
    if not df_filtrado.empty:
        # Gráficos
        fig_incidentes = go.Figure()
        df_total_sector = df_filtrado['Setor'].value_counts()
        df_resolved = df_filtrado[df_filtrado['Status'] == 'Resolvido']
        df_resolved_sector = df_resolved['Setor'].value_counts()
        df_unresolved_sector = df_total_sector - df_resolved_sector.reindex(df_total_sector.index, fill_value=0)

        # Barra de incidentes
        fig_incidentes.add_trace(go.Bar(
            x=df_unresolved_sector.index,
            y=df_unresolved_sector.values,
            name='Pendentes',
            marker_color='salmon',
            text=[f'{val} ({(val / df_total_sector.sum() * 100):.1f}%)' for val in df_unresolved_sector.values],
            textposition='inside',
            textfont=dict(size=14)
        ))

        fig_incidentes.add_trace(go.Bar(
            x=df_resolved_sector.index,
            y=df_resolved_sector.reindex(df_total_sector.index, fill_value=0).values,
            name='Resolvidos',
            marker_color='lightgreen',
            text=[f'{val} ({(val / df_total_sector.sum() * 100):.1f}%)' for val in df_resolved_sector.reindex(df_total_sector.index, fill_value=0).values],
            textposition='inside',
            textfont=dict(size=14)
        ))

        fig_incidentes.add_trace(go.Bar(
            x=df_total_sector.index,
            y=df_total_sector.values,
            name='Total',
            marker_color='skyblue',
            text=[f'{val} ({(val / df_total_sector.sum() * 100):.1f}%)' for val in df_total_sector.values],
            textposition='inside',
            textfont=dict(size=14)
        ))

        fig_incidentes.update_layout(
            title='Comparativo entre Total, Resolvidos e Pendentes',
            xaxis_title='Setor',
            yaxis_title='Quantidade',
            barmode='group',
            legend_title='Tipo de Incidente',
            xaxis_tickangle=-45
        )

        # Exibição do gráfico
        st.plotly_chart(fig_incidentes)

    else:
        st.warning("Não há dados para exibir com os filtros selecionados.")

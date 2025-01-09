import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da página
if 'login' not in st.session_state or not st.session_state.login:
    st.set_page_config(page_title="DataPaws", page_icon="Base/IMG/Designer.jpeg", layout="centered")
else:
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

caminho_arquivo = 'Base/consolidado.xlsx'

if 'login' not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    # Exibição da tela de login
    st.markdown('<div class="login">', unsafe_allow_html=True)
    st.markdown('<h1>DataPaws</h1>', unsafe_allow_html=True)

    with st.form(key='login_form', clear_on_submit=True):
        username = st.text_input("Usuário", placeholder="Username").lower()
        password = st.text_input("Senha", type="password", placeholder="Password")
        submit_button = st.form_submit_button("Entrar")
    
    st.markdown('</div>', unsafe_allow_html=True)

    if submit_button:
        nome_usuario = verificar_login(username, password)
        if nome_usuario:
            st.session_state.login = True
            st.session_state.nome_usuario = nome_usuario
            st.success("Login realizado com sucesso!")
        else:
            st.error("Usuário ou senha incorretos.")
else:
    # Cabeçalho fixo com estilo personalizado
    st.markdown("""
        <style>
        .fixed-header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background-color: white;
            z-index: 1;
            border-bottom: 1px solid #e0e0e0;
            padding: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .fixed-header h1 {
            margin: 0;
            font-size: 24px;
        }
        .fixed-header h2 {
            margin: 0;
            font-size: 18px;
            color: #555;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="fixed-header"><h1>DataPaws</h1><h2>Análise de Dados Consolidados - Backlog</h2><div>', unsafe_allow_html=True)
    st.sidebar.header(f"Bem-vindo, {st.session_state.nome_usuario} ")

    # Sidebar de logout
    if st.sidebar.button("Logout"):
        st.session_state.login = False
        st.success("Logout realizado com sucesso!")
    
    st.markdown('</div></div>', unsafe_allow_html=True)

    # Carregar e processar os dados
    df_dados = carregar_dados(caminho_arquivo)
    df_spn = df_dados['SPN']
    df_iti = df_dados['ITI']

    if 'Setor' not in df_spn.columns or 'Setor' not in df_iti.columns:
        st.error("A coluna 'Setor' não foi encontrada em uma das abas. Verifique os nomes das colunas no arquivo.")
        st.stop()

    # Adicionar coluna "Aba" para distinguir os dados de SPN e ITI
    df_spn['Aba'] = 'SPN'
    df_iti['Aba'] = 'ITI'
    df_consolidado = pd.concat([df_spn, df_iti], ignore_index=True)

    # Barra lateral para filtros
    st.sidebar.header("Filtros")

    # Filtro de Setor com caixas de seleção
    setores_disponiveis = df_consolidado['Setor'].unique()
    setores_selecionados = st.sidebar.multiselect("Setores", setores_disponiveis, default=setores_disponiveis)

    # Definir o título dinamicamente com base nos setores selecionados e adicionar cor para destaque
    titulo_base = "Análise de Dados Consolidados - Backlog"
    if setores_selecionados == ["SPN"]:
        titulo = f"{titulo_base} - <span style='color: #1f77b4;'>SPN</span>"
    elif setores_selecionados == ["ITI"]:
        titulo = f"{titulo_base} - <span style='color: #ff7f0e;'>ITI</span>"
    elif set(setores_selecionados) == set(["SPN", "ITI"]):
        titulo = f"{titulo_base} - <span style='color: #2ca02c;'>Consolidado</span>"
    else:
        titulo = titulo_base  # Caso nenhum setor esteja selecionado (opcional)

    # Exibir o título com estilo personalizado
    st.markdown(f"<h1>{titulo}</h1>", unsafe_allow_html=True)

    # Adicionar coluna de 'Ano' ao DataFrame
    df_consolidado['Ano'] = pd.to_datetime(df_consolidado['Data'], dayfirst=True).dt.year

    # Aplicar filtro de ano ao DataFrame
    df_filtrado = df_consolidado[df_consolidado['Setor'].isin(setores_selecionados)]
    
    # Limpar espaços em branco ao redor do nome de 'Responsavel'
    df_filtrado['Responsavel'] = df_filtrado['Responsavel'].str.strip()

    # Exibir o número de registros após a filtragem
    total_registros = len(df_filtrado)
    
    # Verificar se a coluna 'Status' existe e contar os chamados 'Pendente' ou 'Resolvido'
    total_pendentes = len(df_filtrado[df_filtrado['Status'] == 'Pendente'])
    total_resolvidos = len(df_filtrado[df_filtrado['Status'] == 'Resolvido'])

    # Exibir totais e porcentagens
    percentual_resolvidos = (total_resolvidos / total_registros * 100) if total_registros > 0 else 0
    percentual_pendentes = (total_pendentes / total_registros * 100) if total_registros > 0 else 0

    st.write(f"**Total de Registros:** {total_registros} "
             f"**Resolvidos:** {total_resolvidos} ({percentual_resolvidos:.1f}%) "
             f"**Pendentes:** {total_pendentes} ({percentual_pendentes:.1f}%)")

    # Adicionar gráfico
    # Verificar se há dados após o filtro
    if len(df_filtrado) > 0:
        # Agregar os dados por Backlog e Status
        backlog_por_status = df_filtrado.groupby(['Backlog', 'Status']).size().reset_index(name='Count')

        # Gerar o gráfico de linha
        fig_backlog_status = px.line(
            backlog_por_status,
            x="Backlog",
            y="Count",
            color="Status",  # Aqui é possível adicionar a categoria de 'Status'
            title="Backlog por Status",
            color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c']  # Definindo cores
        )
        st.plotly_chart(fig_backlog_status)
    else:
        st.error("Nenhum dado disponível para os filtros selecionados.")


    if not df_filtrado.empty:
        # Total de incidentes por setor
        df_total_sector = df_filtrado['Setor'].value_counts()
        df_resolved = df_filtrado[df_filtrado['Status'] == 'Resolvido']
        df_resolved_sector = df_resolved['Setor'].value_counts()
        df_unresolved_sector = df_total_sector - df_resolved_sector.reindex(df_total_sector.index, fill_value=0)

        # Criar gráfico de barras
        fig_incidentes = go.Figure()

        # Adicionar a barra de 'Pendentes' (à direita)
        fig_incidentes.add_trace(go.Bar(
            x=df_unresolved_sector.index,
            y=df_unresolved_sector.values,
            name='Pendentes',
            marker_color='salmon',
            text=[f'{val} ({(val / df_total_sector.sum() * 100):.1f}%)' for val in df_unresolved_sector.values],
            textposition='inside',
            textfont=dict(size=14)  # Aumenta o tamanho da fonte dos rótulos
        ))

        # Adicionar a barra de 'Resolvidos' (à esquerda de 'Pendentes')
        fig_incidentes.add_trace(go.Bar(
            x=df_resolved_sector.index,
            y=df_resolved_sector.reindex(df_total_sector.index, fill_value=0).values,
            name='Resolvidos',
            marker_color='lightgreen',
            text=[f'{val} ({(val / df_total_sector.sum() * 100):.1f}%)' for val in df_resolved_sector.reindex(df_total_sector.index, fill_value=0).values],
            textposition='inside',
            textfont=dict(size=14)  # Aumenta o tamanho da fonte dos rótulos
        ))

        # Adicionar a barra de 'Total' (à esquerda de 'Resolvidos')
        fig_incidentes.add_trace(go.Bar(
            x=df_total_sector.index,
            y=df_total_sector.values,
            name='Total',
            marker_color='skyblue',
            text=[f'{val} ({(val / df_total_sector.sum() * 100):.1f}%)' for val in df_total_sector.values],
            textposition='inside',
            textfont=dict(size=14)  # Aumenta o tamanho da fonte dos rótulos
        ))

        fig_incidentes.update_layout(
            title='Comparativo entre Total, Resolvidos e Pendentes',
            xaxis_title='Setor',
            yaxis_title='Quantidade',
            barmode='group',
            legend_title='Tipo de Incidente',
            xaxis_tickangle=-45
        )


        # Gráfico de backlog por status
        if 'Backlog' in df_filtrado.columns:
            backlog_por_status = (
                df_filtrado.groupby(['Backlog', 'Status'])
                .size()
                .unstack(fill_value=0)
                .reset_index()
            )
            
            backlog_por_status['Total'] = backlog_por_status.sum(axis=1, numeric_only=True)

            colors = ['lightgreen', 'red', 'Skyblue'] 
            
            fig_backlog_status = px.line(
                backlog_por_status,
                x='Backlog',
                y=['Resolvido', 'Pendente', 'Total'],
                labels={'Backlog': 'Mês/Ano', 'value': 'Contagem', 'variable': 'Status'},
                title="Distribuição de Incidentes por Status",
                markers=True,
                color_discrete_sequence=colors
            )

            # Manter a legenda
            fig_backlog_status.update_layout(legend_title_text='Status')

            # Adicionando rótulos de dados ao gráfico de linha
            for trace in fig_backlog_status.data:
                trace.text = trace.y  # Adiciona os valores como texto
                trace.textposition = 'top center'  # Posição do texto

            # Adicionando anotações para mostrar os valores
            for trace in fig_backlog_status.data:
                for x, y in zip(backlog_por_status['Backlog'], trace.y):
                    fig_backlog_status.add_annotation(
                        x=x,
                        y=y,
                        text=str(y),
                        showarrow=True,
                        arrowhead=2,
                        ax=0,
                        ay=-10,
                        font=dict(size=14)
                    )

        # Gráfico de desempenho por responsável
        fig_desempenho = go.Figure()
        if 'Responsavel' in df_filtrado.columns:
            df_responsavel_grouped = df_filtrado.drop_duplicates(subset=['Responsavel', 'Incidente']).groupby(['Responsavel', 'Status']).size().unstack(fill_value=0)
            df_responsavel_grouped['Total'] = df_responsavel_grouped.sum(axis=1)
            df_responsavel_grouped['Percentual Resolvidos'] = (df_responsavel_grouped.get('Resolvido', 0) / df_responsavel_grouped['Total']) * 100
            df_responsavel_grouped = df_responsavel_grouped.reset_index()

            # Ordenar o DataFrame pelo total em ordem crescente
            df_responsavel_grouped = df_responsavel_grouped.sort_values(by='Total', ascending=True)

            # Adicionar o gráfico de 'Resolvido' primeiro (barra à esquerda)
            fig_desempenho.add_trace(go.Bar(
                x=df_responsavel_grouped['Responsavel'],
                y=df_responsavel_grouped['Resolvido'],
                name='Resolvidos',
                marker_color='lightgreen',
                text=df_responsavel_grouped['Resolvido'],
                textposition='inside',
                textfont=dict(size=15)  # Fonte maior para os rótulos de texto nas barras
            ))

            # Adicionar o gráfico de 'Total' depois (barra à direita)
            fig_desempenho.add_trace(go.Bar(
                x=df_responsavel_grouped['Responsavel'],
                y=df_responsavel_grouped['Total'],
                name='Total',
                marker_color='lightblue',
                text=df_responsavel_grouped['Total'],
                textposition='inside',
                textfont=dict(size=15)  # Fonte maior para os rótulos de texto nas barras
            ))

            fig_desempenho.update_layout(
                title='Desempenho dos Responsáveis',
                xaxis_title='Responsável',
                yaxis_title='Quantidade',
                barmode='group',  # Modo de agrupamento
                legend_title='Tipo'
            )

            # Adicionar anotações com o percentual de resolvidos
            for i in range(len(df_responsavel_grouped)):
                fig_desempenho.add_annotation(
                    x=df_responsavel_grouped['Responsavel'][i],
                    y=df_responsavel_grouped['Resolvido'][i],
                    text=f"{df_responsavel_grouped['Percentual Resolvidos'][i]:.1f}%",
                    showarrow=True,
                    arrowhead=2,
                    ax=0,
                    ay=-30,
                    font=dict(size=14)
                )

        # Gráfico de pizza
        if 'Responsavel' in df_filtrado.columns:
            df_status = df_filtrado.drop_duplicates(subset=['Responsavel', 'Incidente']).groupby('Responsavel').size()            
            total = df_status.sum()
            percentages = df_status / total * 100
            df_status_grouped = df_status[percentages >= 5]
            other_count = df_status[percentages < 5].sum()
            if other_count > 0:
                df_status_grouped['Outros'] = other_count

            # Gráfico de pizza se houver dados
            if not df_status_grouped.empty:
                fig_responsaveis = px.pie(
                    df_status_grouped,
                    names=df_status_grouped.index,
                    values=df_status_grouped.values,
                    title='Distribuição Backlog por Responsáveis',
                    hole=0.3
                )

                # Adicionando rótulos de dados ao gráfico de pizza
                fig_responsaveis.update_traces(textposition='inside', 
                                               textinfo='percent',
                                               textfont=dict(size=14))

        # Disposição dos gráficos em 3x2
        col1, col2 = st.columns(2)

        with col1:
            st.plotly_chart(fig_incidentes, use_container_width=True)

        with col2:
            if 'Backlog' in df_filtrado.columns:
                st.plotly_chart(fig_backlog_status, use_container_width=True)

        col3, col4 = st.columns(2)

        with col3:
            if 'Responsavel' in df_filtrado.columns and 'fig_responsaveis' in locals():
                st.plotly_chart(fig_responsaveis, use_container_width=True)

        with col4:
            st.plotly_chart(fig_desempenho, use_container_width=True)

    else:
        st.write("Nenhum registro encontrado com os filtros aplicados.")
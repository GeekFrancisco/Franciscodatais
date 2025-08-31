import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
import io 
import numpy as np 

#Carregar variáveis de ambiente
load_dotenv()

# Configuração da página
if 'login' not in st.session_state or not st.session_state.login:
    st.set_page_config(page_title="DataPaws", page_icon="Base/IMG/Designer.jpeg", layout="centered")
else:
    st.set_page_config(page_title="DataPaws", page_icon="Base/IMG/Designer.jpeg", layout="wide")

# Carregar credenciais do .env
usuarios = {
    "emerson": (os.getenv("USERNAME_EMERSON"), "Emerson Cleiton Simette"),
    "willian": (os.getenv("USERNAME_WILLIAN"), "Willian Jones Rios"),
    "rafael": (os.getenv("USERNAME_RAFAEL"), "Rafael Dall'Anese"),
    "admin": (os.getenv("USERNAME_ADMIN"), "Administrador"),
}

setores_por_usuario = {
    "Emerson Cleiton Simette": ["ITI"],
    "Willian Jones Rios": ["SPN"],
    "Rafael Dall'Anese": ["SPN", "ITI"],
    "Administrador": ["SPN", "ITI"],
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
    st.markdown("""<style>.fixed-header {position: fixed; top: 0; left: 0; right: 0; background-color: white; z-index: 1; border-bottom: 1px solid #e0e0e0; padding: 10px; display: flex; justify-content: space-between; align-items: center;} .fixed-header h1 {margin: 0; font-size: 24px;} .fixed-header h2 {margin: 0; font-size: 18px; color: #555;} </style>""", unsafe_allow_html=True)
    st.markdown('<div class="fixed-header"><h1>DataPaws</h1><h2>Análise de Dados Consolidados - Backlog</h2><div>', unsafe_allow_html=True)
    st.sidebar.markdown(f"<b>Bem-vindo</b><br>{st.session_state.nome_usuario}", unsafe_allow_html=True)

    # Sidebar
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

    df_spn['Aba'] = 'SPN'
    df_iti['Aba'] = 'ITI'
    df_consolidado = pd.concat([df_spn, df_iti], ignore_index=True)

    # --- SELETOR DE PÁGINA --- #
    abas = st.tabs(["Dashboard", "Relatórios", "Eficiência"])

    with abas[0]:

        # Segmentação por usuário
        usuario_nome = st.session_state.nome_usuario
        setores_permitidos = setores_por_usuario.get(usuario_nome, ["SPN", "ITI"])
        setores_disponiveis = [s for s in df_consolidado['Setor'].unique() if s in setores_permitidos]

        # Filtros do Dashboard
        st.sidebar.header("Filtros")
        setores_selecionados = st.sidebar.multiselect(
            "Setores", setores_disponiveis, default=setores_disponiveis, key="filtro_dashboard_setor"
        )

        # Definir o título dinamicamente com base nos setores selecionados e adicionar cor para destaque
        titulo_base = "Visão Geral do Backlog"
        if setores_selecionados == ["SPN"]:
            titulo = f"{titulo_base} - <span style='color: #1f77b4;'>SPN</span>"
        elif setores_selecionados == ["ITI"]:
            titulo = f"{titulo_base} - <span style='color: #ff7f0e;'>ITI</span>"
        elif set(setores_selecionados) == set(["SPN", "ITI"]):
            titulo = f"{titulo_base} - <span style='color: #2ca02c;'>Consolidado</span>"
        else:
            titulo = titulo_base  # Caso nenhum setor esteja selecionado (opcional)

        st.markdown(f"<h1>{titulo}</h1>", unsafe_allow_html=True)

        # Adicionar coluna de 'Ano' ao DataFrame, caso ainda não tenha
        df_consolidado['Ano'] = pd.to_datetime(df_consolidado['Data'], dayfirst=True).dt.year  # Corrigido

        # Aplicar filtro de ano ao DataFrame
        df_filtrado = df_consolidado[df_consolidado['Setor'].isin(setores_selecionados)]
        
        # Limpar espaços em branco ao redor do nome de 'Responsavel'
        df_filtrado['Responsavel'] = df_filtrado['Responsavel'].str.strip()

        # Contagem de status
        status_counts = df_filtrado['Status'].value_counts()
        total_registros = len(df_filtrado)
        
        # Contar Resolvido e Pendente
        total_resolvidos = status_counts.get('Resolvido', 0)
        total_pendentes = status_counts.get('Pendente', 0)

        # Exibir totais e porcentagens
        percentual_resolvidos = (total_resolvidos / total_registros * 100) if total_registros > 0 else 0
        percentual_pendentes = (total_pendentes / total_registros * 100) if total_registros > 0 else 0

        st.write(f"**Total de Registros:** {total_registros} "
                 f"**Resolvidos:** {total_resolvidos} ({percentual_resolvidos:.1f}%) "
                 f"**Pendentes:** {total_pendentes} ({percentual_pendentes:.1f}%)")
        
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
                textfont=dict(size=14)
            ))

            # Adicionar a barra de 'Resolvidos' (à esquerda de 'Pendentes')
            fig_incidentes.add_trace(go.Bar(
                x=df_resolved_sector.index,
                y=df_resolved_sector.reindex(df_total_sector.index, fill_value=0).values,
                name='Resolvidos',
                marker_color='lightgreen',
                text=[f'{val} ({(val / df_total_sector.sum() * 100):.1f}%)' for val in df_resolved_sector.reindex(df_total_sector.index, fill_value=0).values],
                textposition='inside',
                textfont=dict(size=14)
            ))

            # Adicionar a barra de 'Total' (à esquerda de 'Resolvidos')
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
            
            # Gráfico de Backlog por Status 
            if 'Backlog' in df_filtrado.columns:
                df_filtrado['Backlog'] = pd.to_datetime(df_filtrado['Backlog'], format='%m/%Y')
                backlog_por_status = (
                    df_filtrado.groupby(['Backlog', 'Status'])
                    .size()
                    .unstack(fill_value=0)
                    .reset_index()
                )
                backlog_por_status = backlog_por_status.sort_values(by='Backlog')
                backlog_por_status['Backlog_str'] = backlog_por_status['Backlog'].dt.strftime('%B/%Y')
                backlog_por_status = backlog_por_status.sort_values(by='Backlog', ascending=True)
                colors = ['lightgreen', 'red']
                fig_backlog_status = px.line(
                    backlog_por_status,
                    x='Backlog_str',
                    y=['Resolvido', 'Pendente'],
                    labels={'Backlog_str': 'Mês/Ano', 'value': 'Contagem', 'variable': 'Status'},
                    title="Distribuição de Incidentes por Status",
                    markers=True,
                    color_discrete_sequence=colors
                )
                if 'Resolvido' in backlog_por_status.columns:
                    media_resolvidos = backlog_por_status['Resolvido'].mean()
                    fig_backlog_status.add_hline(
                        y=media_resolvidos,
                        line_dash="dash",
                        line_color='gray',
                        annotation_text=f"Média Resolvidos: {media_resolvidos:.1f}",
                        annotation_position="top left"
                    )
                fig_backlog_status.update_layout(xaxis=dict(categoryorder='array', categoryarray=backlog_por_status['Backlog_str']))
                fig_backlog_status.update_layout(legend_title_text='Status')
                for trace in fig_backlog_status.data:
                    trace.text = trace.y
                    trace.textposition = 'top center'
                for trace in fig_backlog_status.data:
                    for x, y in zip(backlog_por_status['Backlog_str'], trace.y):
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
                df_responsavel_grouped = (
                    df_filtrado
                    .drop_duplicates(subset=['Responsavel', 'Incidente'])
                    .groupby(['Responsavel', 'Status'])
                    .size()
                    .unstack(fill_value=0)
                )
                df_responsavel_grouped['Total'] = df_responsavel_grouped.sum(axis=1)
                df_responsavel_grouped['Percentual Resolvidos'] = (
                    df_responsavel_grouped.get('Resolvido', 0) / df_responsavel_grouped['Total']
                ) * 100
                df_responsavel_grouped = df_responsavel_grouped.reset_index()
                df_responsavel_maior5 = df_responsavel_grouped[df_responsavel_grouped['Total'] > 5].copy()
                df_responsavel_menor_igual5 = df_responsavel_grouped[df_responsavel_grouped['Total'] <= 5].copy()
                if not df_responsavel_menor_igual5.empty:
                    outros = {
                        'Responsavel': 'Outros',
                        'Resolvido': df_responsavel_menor_igual5.get('Resolvido', 0).sum(),
                        'Pendente': df_responsavel_menor_igual5.get('Pendente', 0).sum(),
                        'Total': df_responsavel_menor_igual5['Total'].sum(),
                    }
                    if outros['Total'] > 0:
                        outros['Percentual Resolvidos'] = (outros['Resolvido'] / outros['Total']) * 100
                    else:
                        outros['Percentual Resolvidos'] = 0
                    df_responsavel_maior5 = pd.concat([df_responsavel_maior5, pd.DataFrame([outros])], ignore_index=True)
                df_responsavel_maior5 = df_responsavel_maior5.sort_values(by='Total', ascending=True)
                fig_desempenho.add_trace(go.Bar(
                    x=df_responsavel_maior5['Responsavel'],
                    y=df_responsavel_maior5.get('Pendente', 0),
                    name='Pendentes',
                    marker_color='salmon',
                    text=df_responsavel_maior5.get('Pendente', 0),
                    textposition='inside',
                    textfont=dict(size=15)
                ))
                fig_desempenho.add_trace(go.Bar(
                    x=df_responsavel_maior5['Responsavel'],
                    y=df_responsavel_maior5.get('Resolvido', 0),
                    name='Resolvidos',
                    marker_color='lightgreen',
                    text=df_responsavel_maior5.get('Resolvido', 0),
                    textposition='inside',
                    textfont=dict(size=15)
                ))
                fig_desempenho.add_trace(go.Bar(
                    x=df_responsavel_maior5['Responsavel'],
                    y=df_responsavel_maior5['Total'],
                    name='Total',
                    marker_color='skyblue',
                    text=df_responsavel_maior5['Total'],
                    textposition='inside',
                    textfont=dict(size=15)
                ))
                fig_desempenho.update_layout(
                    title='Desempenho dos Responsáveis',
                    xaxis_title='Responsável',
                    yaxis_title='Quantidade',
                    barmode='group',
                    legend_title='Tipo'
                )
                for i in range(len(df_responsavel_maior5)):
                    fig_desempenho.add_annotation(
                        x=df_responsavel_maior5['Responsavel'].iloc[i],
                        y=df_responsavel_maior5.get('Resolvido', 0).iloc[i],
                        text=f"{df_responsavel_maior5['Percentual Resolvidos'].iloc[i]:.1f}%",
                        showarrow=False,
                        font=dict(size=14),
                        yshift=10
                    )
            if 'Responsavel' in df_filtrado.columns:
                df_status = (
                    df_filtrado
                    .drop_duplicates(subset=['Responsavel', 'Incidente'])
                    .groupby('Responsavel')
                    .size()
                )
                df_status_maior5 = df_status[df_status > 5]
                outros_count = df_status[df_status <= 5].sum()
                if outros_count > 0:
                    df_status_pizza = pd.concat([df_status_maior5, pd.Series([outros_count], index=['Outros'])])
                else:
                    df_status_pizza = df_status_maior5
                if not df_status_pizza.empty:
                    fig_responsaveis = px.pie(
                        df_status_pizza,
                        names=df_status_pizza.index,
                        values=df_status_pizza.values,
                        title='Distribuição Backlog por Responsáveis',
                        hole=0.3
                    )
                    fig_responsaveis.update_traces(
                        textposition='inside',
                        textinfo='percent',
                        textfont=dict(size=14)
                    )
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

    with abas[1]:

            # Segmentação por usuário
            usuario_nome = st.session_state.nome_usuario
            setores_permitidos = setores_por_usuario.get(usuario_nome, ["SPN", "ITI"])
            df_consolidado_relatorio = df_consolidado[df_consolidado['Setor'].isin(setores_permitidos)]

            # Inicializar filtros no session_state se não existirem
            if "filtro_relatorio_setor" not in st.session_state:
                st.session_state["filtro_relatorio_setor"] = list(df_consolidado_relatorio['Setor'].unique())
            if "filtro_relatorio_status" not in st.session_state:
                st.session_state["filtro_relatorio_status"] = ["Resolvido", "Pendente"]
            if "filtro_relatorio_responsavel" not in st.session_state:
                st.session_state["filtro_relatorio_responsavel"] = ["Todos"]
            if "filtro_relatorio_colunas" not in st.session_state:
                st.session_state["filtro_relatorio_colunas"] = ["Todos"]

            # 1. TÍTULO (antes dos filtros)
            setor_filtro = st.session_state["filtro_relatorio_setor"]
            titulo_base = "Consulta Detalhada do Backlog"
            if setor_filtro == ["SPN"]:
                titulo = f"{titulo_base} - <span style='color: #1f77b4;'>SPN</span>"
            elif setor_filtro == ["ITI"]:
                titulo = f"{titulo_base} - <span style='color: #ff7f0e;'>ITI</span>"
            elif set(setor_filtro) == set(["SPN", "ITI"]):
                titulo = f"{titulo_base} - <span style='color: #2ca02c;'>Consolidado</span>"
            elif len(setor_filtro) == 0:
                titulo = titulo_base
            else:
                titulo = f"{titulo_base} - <span style='color: #888;'>Filtrado</span>"

            st.markdown(f"<h1>{titulo}</h1>", unsafe_allow_html=True)

            # 2. FILTROS NO GRID
            st.markdown("### Filtros do Relatório")
            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

            with col1:
                setor_filtro = st.multiselect(
                    "Setor", 
                    df_consolidado_relatorio['Setor'].unique(),
                    key="filtro_relatorio_setor"
                )
            with col2:
                responsaveis_disponiveis = sorted(df_consolidado_relatorio[df_consolidado_relatorio['Setor'].isin(setor_filtro)]['Responsavel'].unique())
                opcoes_responsavel = ["Todos"] + responsaveis_disponiveis
                responsavel_filtro = st.multiselect(
                    "Responsável", 
                    opcoes_responsavel,
                    key="filtro_relatorio_responsavel"
                )
                if "Todos" in responsavel_filtro or not responsavel_filtro:
                    responsaveis_filtrados = responsaveis_disponiveis
                else:
                    responsaveis_filtrados = responsavel_filtro
            with col3:
                status_opcoes = ["Resolvido", "Pendente"]
                status_filtro = st.multiselect(
                    "Status",
                    status_opcoes,
                    key="filtro_relatorio_status"
                )
            with col4:
                colunas = list(df_consolidado_relatorio.columns)
                opcoes_colunas = ["Todos"] + colunas
                colunas_exibir = st.multiselect(
                    "Colunas para exibir", 
                    opcoes_colunas,
                    key="filtro_relatorio_colunas"
                )
                if "Todos" in colunas_exibir or not colunas_exibir:
                    colunas_exibir = colunas

            # 3. RELATÓRIO
            df_relatorio = df_consolidado_relatorio[
                (df_consolidado_relatorio['Setor'].isin(setor_filtro)) &
                (df_consolidado_relatorio['Status'].isin(st.session_state.get("filtro_relatorio_status", []))) &
                (df_consolidado_relatorio['Responsavel'].isin(responsaveis_filtrados))
            ].copy()

            # Corrigir coluna Ano para não mostrar separador de milhar
            if 'Ano' in df_relatorio.columns:
                df_relatorio['Ano'] = df_relatorio['Ano'].astype(str).str.replace(',', '')

            # Corrigir coluna Incidente para não mostrar separador de milhar
            if 'Incidente' in df_relatorio.columns and pd.api.types.is_numeric_dtype(df_relatorio['Incidente']):
                df_relatorio['Incidente'] = df_relatorio['Incidente'].astype(str).str.replace(',', '')

            # Centralizar colunas via CSS
            st.markdown("""
                <style>
                .stDataFrame td, .stDataFrame th {
                    text-align: center !important;
                    vertical-align: middle !important;
                }
                </style>
            """, unsafe_allow_html=True)

            # Exportar para Excel alinhado à direita, na mesma linha do relatório
            col5, col6 = st.columns([0.8, 0.2])
            with col5:
                st.write(f"**Total de registros encontrados:** {len(df_relatorio)}")
            with col6:
                excel_buffer = io.BytesIO()
                df_relatorio[colunas_exibir].to_excel(excel_buffer, index=False)
                st.download_button(
                    label="Exportar para Excel",
                    data=excel_buffer.getvalue(),
                    file_name='Backlog__Detalhado.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    use_container_width=True,
                )

            # Relatório com altura maior
            st.dataframe(df_relatorio[colunas_exibir], use_container_width=True, height=700)
        
    # ...existing code...
    with abas[2]:
        st.markdown("<h1>Eficiência Semanal e Projeção</h1>", unsafe_allow_html=True)

        # Filtros iguais ao Dashboard
        setores_disponiveis = [s for s in df_consolidado['Setor'].unique() if s in setores_permitidos]
        setores_selecionados = st.multiselect(
            "Setores", setores_disponiveis, default=setores_disponiveis, key="filtro_eficiencia_setor"
        )

        responsaveis_disponiveis = sorted(df_consolidado[df_consolidado['Setor'].isin(setores_selecionados)]['Responsavel'].unique())
        responsavel_selecionado = st.multiselect(
            "Responsável", ["Todos"] + responsaveis_disponiveis, default=["Todos"], key="filtro_eficiencia_responsavel"
        )
        if "Todos" in responsavel_selecionado or not responsavel_selecionado:
            responsaveis_filtrados = responsaveis_disponiveis
        else:
            responsaveis_filtrados = responsavel_selecionado

        status_opcoes = ["Resolvido", "Pendente"]
        status_selecionado = st.multiselect(
            "Status", status_opcoes, default=status_opcoes, key="filtro_eficiencia_status"
        )

        # Filtrar dados conforme seleção
        df_filtrado = df_consolidado[
            (df_consolidado['Setor'].isin(setores_selecionados)) &
            (df_consolidado['Responsavel'].isin(responsaveis_filtrados)) &
            (df_consolidado['Status'].isin(status_selecionado))
        ].copy()

        # Garantir que 'Semana' é numérica
        df_filtrado['Semana'] = pd.to_numeric(df_filtrado['Semana'], errors='coerce')

        # Eficiência semanal (% resolvidos)
        eficiencia_semanal = (
            df_filtrado.groupby(['Ano', 'Semana'])['Status']
            .apply(lambda x: (x == 'Resolvido').mean() * 100)
            .reset_index(name='Eficiência (%)')
        )

        # Projeção: média dos últimos 12 semanas (3 meses)
        ultimas_semanas = eficiencia_semanal.sort_values(['Ano', 'Semana'], ascending=[False, False]).head(12)
        media_eficiencia = ultimas_semanas['Eficiência (%)'].mean() if not ultimas_semanas.empty else 0

        # Criar semanas futuras como placeholder
        semana_max = eficiencia_semanal['Semana'].max()
        ano_atual = eficiencia_semanal['Ano'].max()
        semanas_futuras = pd.DataFrame({
            'Ano': [ano_atual]*4,
            'Semana': [semana_max + i for i in range(1, 5)],
            'Eficiência (%)': [media_eficiencia]*4
        })

        # Concatenar para mostrar no gráfico
        eficiencia_proj = pd.concat([eficiencia_semanal, semanas_futuras], ignore_index=True)

        fig = px.line(
            eficiencia_proj,
            x='Semana',
            y='Eficiência (%)',
            color='Ano',
            markers=True,
            title='Eficiência Semanal (%) e Projeção Próximas Semanas',
            text='Eficiência (%)'
        )
        fig.update_traces(textposition="top center")

        # Destacar projeção
        fig.add_scatter(
            x=semanas_futuras['Semana'],
            y=semanas_futuras['Eficiência (%)'],
            mode='markers+lines',
            name='Projeção',
            line=dict(dash='dash', color='gray'),
            marker=dict(symbol='diamond', color='gray', size=10)
        )

        st.plotly_chart(fig, use_container_width=True)
        st.write(f"Projeção baseada na média dos últimos 3 meses: **{media_eficiencia:.1f}%**")
    # ...existing code...
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
import io 

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da página
if 'login' not in st.session_state or not st.session_state.login:
    st.set_page_config(page_title="DataPaws Moderno", page_icon="📊", layout="centered")
else:
    st.set_page_config(page_title="DataPaws Moderno", page_icon="📊", layout="wide")

# CSS Moderno
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .main .block-container {
        padding-top: 0 !important;
        padding-bottom: 2rem;
        max-width: 100%;
        margin-top: 0 !important;
    }
    
    /* Remove espaçamento superior em telas de login */
    .main .block-container > div:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Background com gradiente moderno */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Remove header padrão do Streamlit */
    header[data-testid="stHeader"] {
        height: 0 !important;
        min-height: 0 !important;
        max-height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        display: none !important;
    }
    
    /* Header moderno */
    .modern-header {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .modern-header h1 {
        font-family: 'Inter', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
    }
    
    /* Cards modernos */
    .modern-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .modern-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    }
    
    /* Métricas modernas */
    .metric-card {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
        margin: 0.5rem;
    }
    
    .metric-value {
        font-family: 'Inter', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
    }
    
    .metric-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        font-weight: 500;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
    
    /* Sidebar moderno */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    
    /* Tabs modernos */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 8px;
        backdrop-filter: blur(10px);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 24px;
        background: rgba(255, 255, 255, 0.1);
        border: none;
        border-radius: 10px;
        color: white;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(255, 255, 255, 0.9);
        color: #667eea;
        font-weight: 600;
    }
    
    /* Botões modernos */
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border: none;
        border-radius: 10px;
        color: white;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        padding: 0.75rem 2rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Login simples */
    .login-container {
        background: white;
        border-radius: 8px;
        padding: 2rem;
        max-width: 400px;
        margin: 0 auto;
        margin-top: 1rem;
    }
    
    .login-title {
        font-family: 'Inter', sans-serif;
        font-size: 2rem;
        font-weight: 600;
        text-align: center;
        color: #333;
        margin-bottom: 2rem;
        margin-top: 0;
    }
    
    /* Modo TV - Estilos para televisão */
    .tv-mode {
        font-size: 1.2em !important;
    }
    
    .tv-mode .metric-card {
        padding: 2.5rem !important;
        margin: 1rem !important;
    }
    
    .tv-mode .metric-value {
        font-size: 3.5rem !important;
    }
    
    .tv-mode .metric-label {
        font-size: 1.2rem !important;
    }
    
    .tv-mode h1 {
        font-size: 3rem !important;
        margin-bottom: 2rem !important;
    }
    
    .tv-mode h2 {
        font-size: 2.2rem !important;
    }
    
    .tv-mode h3 {
        font-size: 1.8rem !important;
    }
</style>
""", unsafe_allow_html=True)

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
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="login-title">DataPaws</h1>', unsafe_allow_html=True)

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
            st.success("✅ Login realizado com sucesso!")
            st.rerun()
        else:
            st.error("❌ Usuário ou senha incorretos.")
else:
    # Sidebar moderno
    st.sidebar.markdown(f"**👋 Bem-vindo**\n\n**{st.session_state.nome_usuario}**")
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state.login = False
        st.rerun()

    # Carregar e processar os dados
    df_dados = carregar_dados(caminho_arquivo)
    df_spn = df_dados['SPN']
    df_iti = df_dados['ITI']

    if 'Setor' not in df_spn.columns or 'Setor' not in df_iti.columns:
        st.error("❌ A coluna 'Setor' não foi encontrada. Verifique o arquivo.")
        st.stop()

    df_spn['Aba'] = 'SPN'
    df_iti['Aba'] = 'ITI'
    df_consolidado = pd.concat([df_spn, df_iti], ignore_index=True)

    # Tabs principais
    tab1, tab2 = st.tabs(["📈 Dashboard", "📋 Relatórios"])

    with tab1:
        # Segmentação por usuário
        usuario_nome = st.session_state.nome_usuario
        setores_permitidos = setores_por_usuario.get(usuario_nome, ["SPN", "ITI"])
        setores_disponiveis = [s for s in df_consolidado['Setor'].unique() if s in setores_permitidos]

        # Filtros do Dashboard
        st.sidebar.header("🎛️ Filtros")
        
        # Modo TV - Alternância automática
        modo_tv = st.sidebar.checkbox("📺 Modo TV (Alternância Automática)", key="modo_tv")
        
        if modo_tv:
            # Configurações do modo TV
            tempo_alternancia = st.sidebar.slider("⏱️ Tempo de alternância (segundos)", 5, 30, 10)
            
            # Inicializar estado se não existir
            if 'tv_setor_atual' not in st.session_state:
                st.session_state.tv_setor_atual = 0  # 0=SPN, 1=ITI, 2=Consolidado
            if 'tv_ultimo_update' not in st.session_state:
                import time
                st.session_state.tv_ultimo_update = time.time()
            
            # Verificar se é hora de alternar
            import time
            tempo_atual = time.time()
            tempo_decorrido = tempo_atual - st.session_state.tv_ultimo_update
            
            if tempo_decorrido >= tempo_alternancia:
                # Alternar setor (ciclo: SPN -> ITI -> Consolidado -> SPN)
                st.session_state.tv_setor_atual = (st.session_state.tv_setor_atual + 1) % 3
                st.session_state.tv_ultimo_update = tempo_atual
                st.rerun()
            
            # Definir setores selecionados baseado no estado atual
            opcoes_tv = [
                (["SPN"], "SPN"),
                (["ITI"], "ITI"), 
                (["SPN", "ITI"], "Consolidado")
            ]
            setores_selecionados, nome_exibicao = opcoes_tv[st.session_state.tv_setor_atual]
            
            # Calcular tempo restante
            tempo_restante = tempo_alternancia - tempo_decorrido
            
            # Próximo na sequência
            proximo_indice = (st.session_state.tv_setor_atual + 1) % 3
            proximo_nome = opcoes_tv[proximo_indice][1]
            
            # Mostrar informações do modo TV com contador
            st.sidebar.success(f"""🔄 **Modo TV Ativo**
            
📊 **Exibindo:** {nome_exibicao}
⏭️ **Próximo:** {proximo_nome}
⏰ **Tempo restante:** {tempo_restante:.0f}s
            
🔄 **Sequência:** SPN → ITI → Consolidado""")
            
            # Aplicar classe CSS para modo TV
            st.markdown('<div class="tv-mode">', unsafe_allow_html=True)
            
            # Auto-refresh inteligente - só recarrega quando necessário
            # Força alternação quando tempo acabar ou a cada segundo para atualizar contador
            if tempo_restante <= 0 or int(tempo_restante) != st.session_state.get('ultimo_segundo', -1):
                st.session_state.ultimo_segundo = int(tempo_restante)
                st.rerun()
            
        else:
            # Limpar estado do modo TV quando desabilitado
            if 'tv_setor_atual' in st.session_state:
                del st.session_state.tv_setor_atual
            if 'tv_ultimo_update' in st.session_state:
                del st.session_state.tv_ultimo_update
                
            setores_selecionados = st.sidebar.multiselect(
                "🏢 Setores", setores_disponiveis, default=setores_disponiveis, key="filtro_dashboard_setor"
            )
        
        # Título dinâmico baseado nos setores selecionados
        if modo_tv:
            # No modo TV, usar o nome da exibição atual
            opcoes_tv = [
                (["SPN"], "SPN"),
                (["ITI"], "ITI"), 
                (["SPN", "ITI"], "Consolidado")
            ]
            _, nome_exibicao = opcoes_tv[st.session_state.tv_setor_atual]
            st.title(f"📊 Visão Geral do Backlog - {nome_exibicao}")
        else:
            if len(setores_selecionados) == 1:
                if setores_selecionados[0] == "SPN":
                    st.title("📊 2025 - Visão Geral do Backlog - SPN")
                elif setores_selecionados[0] == "ITI":
                    st.title("📊 2025 - Visão Geral do Backlog - ITI")
                else:
                    st.title("📊 2025 - Visão Geral do Backlog - Consolidado")
            else:
                st.title("📊 2025 - Visão Geral do Backlog - Consolidado")

        # Processar dados
        df_consolidado['Ano'] = pd.to_datetime(df_consolidado['Data'], dayfirst=True).dt.year
        df_filtrado = df_consolidado[df_consolidado['Setor'].isin(setores_selecionados)]
        df_filtrado['Responsavel'] = df_filtrado['Responsavel'].str.strip()

        # Métricas principais
        status_counts = df_filtrado['Status'].value_counts()
        total_registros = len(df_filtrado)
        total_resolvidos = status_counts.get('Resolvido', 0)
        total_pendentes = status_counts.get('Pendente', 0)
        percentual_resolvidos = (total_resolvidos / total_registros * 100) if total_registros > 0 else 0
        percentual_pendentes = (total_pendentes / total_registros * 100) if total_registros > 0 else 0

        # Cards de métricas
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        
        with col_m1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{total_registros}</div>
                <div class="metric-label">📊 Total de Registros</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_m2:
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #66BB6A, #4CAF50);">
                <div class="metric-value">{total_resolvidos}</div>
                <div class="metric-label">✅ Resolvidos ({percentual_resolvidos:.1f}%)</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_m3:
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #EF5350, #E53935);">
                <div class="metric-value">{total_pendentes}</div>
                <div class="metric-label">⏳ Pendentes ({percentual_pendentes:.1f}%)</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_m4:
            eficiencia = (total_resolvidos / total_registros * 100) if total_registros > 0 else 0
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #9C27B0, #8e24aa);">
                <div class="metric-value">{eficiencia:.1f}%</div>
                <div class="metric-label">🎯 Eficiência</div>
            </div>
            """, unsafe_allow_html=True)
        
        
        if not df_filtrado.empty:
            # Gráfico 1: Comparativo por Setor
            
            df_total_sector = df_filtrado['Setor'].value_counts()
            df_resolved = df_filtrado[df_filtrado['Status'] == 'Resolvido']
            df_resolved_sector = df_resolved['Setor'].value_counts()
            df_unresolved_sector = df_total_sector - df_resolved_sector.reindex(df_total_sector.index, fill_value=0)

            fig_incidentes = go.Figure()
            
            # Cores modernas
            colors = {
                'Total': '#667eea',
                'Resolvidos': '#66BB6A', 
                'Pendentes': '#EF5350'
            }

            fig_incidentes.add_trace(go.Bar(
                x=df_total_sector.index,
                y=df_total_sector.values,
                name='Total',
                marker_color=colors['Total'],
                text=[f'{val}' for val in df_total_sector.values],
                textposition='inside',
                textfont=dict(size=14, color='white')
            ))

            fig_incidentes.add_trace(go.Bar(
                x=df_resolved_sector.index,
                y=df_resolved_sector.reindex(df_total_sector.index, fill_value=0).values,
                name='Resolvidos',
                marker_color=colors['Resolvidos'],
                text=[f'{val}' for val in df_resolved_sector.reindex(df_total_sector.index, fill_value=0).values],
                textposition='inside',
                textfont=dict(size=14, color='white')
            ))

            fig_incidentes.add_trace(go.Bar(
                x=df_unresolved_sector.index,
                y=df_unresolved_sector.values,
                name='Pendentes',
                marker_color=colors['Pendentes'],
                text=[f'{val}' for val in df_unresolved_sector.values],
                textposition='inside',
                textfont=dict(size=14, color='white')
            ))

            fig_incidentes.update_layout(
                    title={
                        'text': '📊 Comparativo: Total vs Resolvidos vs Pendentes por Setor',
                        'x': 0,
                        'font': {'size': 18, 'family': 'Inter'}
                    },
                xaxis_title='Setor',
                yaxis_title='Quantidade',
                barmode='group',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter'),
                xaxis=dict(gridcolor='white', gridwidth=1),
                yaxis=dict(gridcolor='white', gridwidth=1),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # Gráfico 2: Evolução do Backlog
            if 'Backlog' in df_filtrado.columns:
                df_filtrado_copy = df_filtrado.copy()
                df_filtrado_copy['Backlog'] = pd.to_datetime(df_filtrado_copy['Backlog'], format='%m/%Y')
                backlog_por_status = (
                    df_filtrado_copy.groupby(['Backlog', 'Status'])
                    .size()
                    .unstack(fill_value=0)
                    .reset_index()
                )
                backlog_por_status = backlog_por_status.sort_values(by='Backlog')
                backlog_por_status['Backlog_str'] = backlog_por_status['Backlog'].dt.strftime('%B/%Y')
                
                fig_backlog_status = go.Figure()
                
                if 'Resolvido' in backlog_por_status.columns:
                    fig_backlog_status.add_trace(go.Scatter(
                        x=backlog_por_status['Backlog_str'],
                        y=backlog_por_status['Resolvido'],
                        mode='lines+markers+text',
                        name='Resolvido',
                        line=dict(color='#66BB6A', width=3),
                        marker=dict(size=8),
                        text=backlog_por_status['Resolvido'],
                        textposition='top center'
                    ))
                    
                    media_resolvidos = backlog_por_status['Resolvido'].mean()
                    fig_backlog_status.add_hline(
                        y=media_resolvidos,
                        line_dash="dash",
                        line_color='#FFC107',
                        annotation_text=f"Média: {media_resolvidos:.1f}",
                        annotation_position="top left"
                    )
                
                if 'Pendente' in backlog_por_status.columns:
                    fig_backlog_status.add_trace(go.Scatter(
                        x=backlog_por_status['Backlog_str'],
                        y=backlog_por_status['Pendente'],
                        mode='lines+markers+text',
                        name='Pendente',
                        line=dict(color='#EF5350', width=3),
                        marker=dict(size=8),
                        text=backlog_por_status['Pendente'],
                        textposition='top center'
                    ))

                fig_backlog_status.update_layout(
                    title={
                        'text': '📈 Evolução do Backlog por Status ao Longo do Tempo',
                        'x': 0,
                        'font': {'size': 18, 'family': 'Inter'}
                    },
                    xaxis_title='Período',
                    yaxis_title='Quantidade',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Inter'),
                    xaxis=dict(gridcolor='white', gridwidth=1),
                    yaxis=dict(gridcolor='white', gridwidth=1),
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
            
            # Gráfico 3: Distribuição por Responsáveis (Pizza)
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
                    # Calcular percentuais para a legenda
                    total_valores = df_status_pizza.sum()
                    percentuais = (df_status_pizza / total_valores * 100).round(1)
                    
                    # Criar labels customizados com nome + percentual
                    labels_customizados = [f"{nome} ({perc}%)" for nome, perc in zip(df_status_pizza.index, percentuais)]
                    
                    fig_responsaveis = px.pie(
                        df_status_pizza,
                        names=labels_customizados,
                        values=df_status_pizza.values,
                        title='🥧 Distribuição do Backlog por Responsáveis',
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig_responsaveis.update_traces(
                        textposition='inside',
                        textinfo='percent',
                        textfont=dict(size=12, family='Inter')
                    )
                    fig_responsaveis.update_layout(
                        title={
                            'x': 0,
                            'font': {'size': 18, 'family': 'Inter'}
                        },
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(family='Inter')
                    )
            
            # Gráfico 4: Desempenho Individual
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
                    df_responsavel_maior5 = pd.concat([df_responsavel_maior5, pd.DataFrame([outros])], ignore_index=True)
                
                df_responsavel_maior5 = df_responsavel_maior5.sort_values(by='Total', ascending=True)
                
                fig_desempenho.add_trace(go.Bar(
                    x=df_responsavel_maior5['Responsavel'],
                    y=df_responsavel_maior5['Total'],
                    name='Total',
                    marker_color='#667eea',
                    text=df_responsavel_maior5['Total'],
                    textposition='inside',
                    textfont=dict(size=12, color='white')
                ))
                
                fig_desempenho.add_trace(go.Bar(
                    x=df_responsavel_maior5['Responsavel'],
                    y=df_responsavel_maior5.get('Resolvido', 0),
                    name='Resolvidos',
                    marker_color='#66BB6A',
                    text=df_responsavel_maior5.get('Resolvido', 0),
                    textposition='inside',
                    textfont=dict(size=12, color='white')
                ))
                
                fig_desempenho.add_trace(go.Bar(
                    x=df_responsavel_maior5['Responsavel'],
                    y=df_responsavel_maior5.get('Pendente', 0),
                    name='Pendentes',
                    marker_color='#EF5350',
                    text=df_responsavel_maior5.get('Pendente', 0),
                    textposition='inside',
                    textfont=dict(size=12, color='white')
                ))
                
                fig_desempenho.update_layout(
                    title={
                        'text': '👥 Desempenho Individual dos Responsáveis',
                        'x': 0,
                        'font': {'size': 18, 'family': 'Inter'}
                    },
                    xaxis_title='Responsável',
                    yaxis_title='Quantidade',
                    barmode='group',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Inter'),
                    xaxis=dict(gridcolor='white', gridwidth=1),
                    yaxis=dict(gridcolor='white', gridwidth=1),
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )

            # Layout dos gráficos em grid 2x2
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
            st.warning("⚠️ Nenhum registro encontrado com os filtros aplicados.")
        
        # Fechar div do modo TV se estiver ativo
        if modo_tv:
            st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        # Segmentação por usuário para relatórios
        usuario_nome = st.session_state.nome_usuario
        setores_permitidos = setores_por_usuario.get(usuario_nome, ["SPN", "ITI"])
        df_consolidado_relatorio = df_consolidado[df_consolidado['Setor'].isin(setores_permitidos)]

        # Inicializar filtros no session_state
        if "filtro_relatorio_setor" not in st.session_state:
            st.session_state["filtro_relatorio_setor"] = list(df_consolidado_relatorio['Setor'].unique())
        if "filtro_relatorio_status" not in st.session_state:
            st.session_state["filtro_relatorio_status"] = ["Resolvido", "Pendente"]
        if "filtro_relatorio_responsavel" not in st.session_state:
            st.session_state["filtro_relatorio_responsavel"] = ["Todos"]
        if "filtro_relatorio_colunas" not in st.session_state:
            st.session_state["filtro_relatorio_colunas"] = ["Todos"]

        # Título dinâmico
        setor_filtro = st.session_state["filtro_relatorio_setor"]
        if setor_filtro == ["SPN"]:
            titulo = "📋 Relatório Detalhado - <span style='color: #1f77b4;'>SPN</span>"
        elif setor_filtro == ["ITI"]:
            titulo = "📋 Relatório Detalhado - <span style='color: #ff7f0e;'>ITI</span>"
        elif set(setor_filtro) == set(["SPN", "ITI"]):
            titulo = "📋 Relatório Detalhado - <span style='color: #2ca02c;'>Consolidado</span>"
        else:
            titulo = "📋 Relatório Detalhado"

        st.markdown(f"<h2 style='text-align: center; margin-bottom: 2rem;'>{titulo}</h2>", unsafe_allow_html=True)

        # Filtros do relatório
        st.markdown("### 🎛️ Filtros Avançados")
        col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

        with col1:
            setor_filtro = st.multiselect(
                "🏢 Setor", 
                df_consolidado_relatorio['Setor'].unique(),
                key="filtro_relatorio_setor"
            )
        
        with col2:
            responsaveis_disponiveis = sorted(df_consolidado_relatorio[df_consolidado_relatorio['Setor'].isin(setor_filtro)]['Responsavel'].unique())
            opcoes_responsavel = ["Todos"] + responsaveis_disponiveis
            responsavel_filtro = st.multiselect(
                "👤 Responsável", 
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
                "📊 Status",
                status_opcoes,
                key="filtro_relatorio_status"
            )
        
        with col4:
            colunas = list(df_consolidado_relatorio.columns)
            opcoes_colunas = ["Todos"] + colunas
            colunas_exibir = st.multiselect(
                "📋 Colunas",
                opcoes_colunas,
                key="filtro_relatorio_colunas"
            )
            if "Todos" in colunas_exibir or not colunas_exibir:
                colunas_exibir = colunas
            else:
                colunas_exibir = [col for col in colunas_exibir if col in colunas]

        # Aplicar filtros
        df_relatorio = df_consolidado_relatorio.copy()
        
        if setor_filtro:
            df_relatorio = df_relatorio[df_relatorio['Setor'].isin(setor_filtro)]
        
        if responsaveis_filtrados:
            df_relatorio = df_relatorio[df_relatorio['Responsavel'].isin(responsaveis_filtrados)]
        
        if status_filtro:
            df_relatorio = df_relatorio[df_relatorio['Status'].isin(status_filtro)]

        # Exibir estatísticas
        st.markdown("### 📊 Estatísticas do Relatório")
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        
        with col_stat1:
            st.metric("📋 Total de Registros", len(df_relatorio))
        
        with col_stat2:
            if len(df_relatorio) > 0:
                resolvidos_rel = len(df_relatorio[df_relatorio['Status'] == 'Resolvido'])
                perc_resolvidos = (resolvidos_rel / len(df_relatorio)) * 100
                st.metric("✅ Resolvidos", f"{resolvidos_rel} ({perc_resolvidos:.1f}%)")
            else:
                st.metric("✅ Resolvidos", "0 (0%)")
        
        with col_stat3:
            if len(df_relatorio) > 0:
                pendentes_rel = len(df_relatorio[df_relatorio['Status'] == 'Pendente'])
                perc_pendentes = (pendentes_rel / len(df_relatorio)) * 100
                st.metric("⏳ Pendentes", f"{pendentes_rel} ({perc_pendentes:.1f}%)")
            else:
                st.metric("⏳ Pendentes", "0 (0%)")

        # Exibir dados
        st.markdown("### 📋 Dados Detalhados")
        if not df_relatorio.empty:
            # Botão de download
            csv = df_relatorio[colunas_exibir].to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"relatorio_backlog_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            # Exibir tabela
            st.dataframe(
                df_relatorio[colunas_exibir], 
                use_container_width=True, 
                height=600
            )
        else:
            st.warning("⚠️ Nenhum registro encontrado com os filtros aplicados.")
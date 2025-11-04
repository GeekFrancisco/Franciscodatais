"""
Dashboard de Análise de Backlog
Versão refatorada com melhor organização e performance
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
import io
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# ==================== CONFIGURAÇÕES E CONSTANTES ====================

# Carregar variáveis de ambiente
load_dotenv()

# Modo mínimo: exibe apenas o essencial (Dashboard)
# Pode ser controlado via .env com MINIMAL_MODE=true/false
MINIMAL_MODE = str(os.getenv("MINIMAL_MODE", "true")).lower() in ("true", "1", "yes", "y", "sim")

# Configurações da aplicação
APP_CONFIG = {
    'title': 'Dashboard de Backlog',
    'icon': 'data/base/IMG/Designer.jpeg',
    'data_file': 'data/base/consolidado.xlsx'
}
TOP_N_RESPONSAVEIS = 8
MOV_AVG_WINDOW = 3

# Cores para gráficos (esquema claro)
COLORS = {
    'primary': '#2E86AB',      # Azul moderno
    'secondary': '#A23B72',    # Rosa/Roxo
    'success': '#F18F01',      # Laranja vibrante
    'pending': '#C73E1D',      # Vermelho
    'resolved': '#2ECC71',     # Verde vibrante
    'total': '#3498DB',        # Azul claro
    'neutral': '#95A5A6',      # Cinza moderno
    'background': '#F8F9FA',   # Fundo claro
    'text': '#2C3E50'          # Texto escuro
}

# Configuração de usuários e setores
USUARIOS = {
    "emerson": (os.getenv("USERNAME_EMERSON"), "Emerson Cleiton Simette"),
    "willian": (os.getenv("USERNAME_WILLIAN"), "Willian Jones Rios"),
    "rafael": (os.getenv("USERNAME_RAFAEL"), "Rafael Dall'Anese"),
    "admin": (os.getenv("USERNAME_ADMIN"), "Administrador"),
}

SETORES_POR_USUARIO = {
    "Emerson Cleiton Simette": ["ITI"],
    "Willian Jones Rios": ["SPN"],
    "Rafael Dall'Anese": ["SPN", "ITI"],
    "Administrador": ["SPN", "ITI"],
}

# ==================== FUNÇÕES DE UTILIDADE ====================

def configurar_pagina() -> None:
    """Configura a página do Streamlit baseado no estado de login."""
    layout = "wide" if st.session_state.get('login', False) else "centered"
    st.set_page_config(
        page_title=APP_CONFIG['title'],
        page_icon=APP_CONFIG['icon'],
        layout=layout
    )

def verificar_login(username: str, password: str) -> Optional[str]:
    """
    Verifica as credenciais do usuário.
    
    Args:
        username: Nome de usuário
        password: Senha
        
    Returns:
        Nome completo do usuário se válido, None caso contrário
    """
    if username in USUARIOS and password == USUARIOS[username][0]:
        return USUARIOS[username][1]
    return None

@st.cache_data
def carregar_dados(caminho_arquivo: str) -> Dict[str, pd.DataFrame]:
    """
    Carrega dados do arquivo Excel com cache.
    
    Args:
        caminho_arquivo: Caminho para o arquivo Excel
        
    Returns:
        Dicionário com os DataFrames das abas
    """
    try:
        return pd.read_excel(caminho_arquivo, sheet_name=None)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return {}

def processar_dados_consolidados(df_dados: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Processa e consolida os dados das abas SPN e ITI.
    
    Args:
        df_dados: Dicionário com DataFrames das abas
        
    Returns:
        DataFrame consolidado
    """
    try:
        df_spn = df_dados['SPN'].copy()
        df_iti = df_dados['ITI'].copy()
        
        # Verificar se a coluna 'Setor' existe
        if 'Setor' not in df_spn.columns or 'Setor' not in df_iti.columns:
            st.error("A coluna 'Setor' não foi encontrada. Verifique o arquivo.")
            st.stop()
        
        # Adicionar identificação da aba
        df_spn['Aba'] = 'SPN'
        df_iti['Aba'] = 'ITI'
        
        # Consolidar dados
        df_consolidado = pd.concat([df_spn, df_iti], ignore_index=True)
        
        # Processar coluna de data se existir
        if 'Data' in df_consolidado.columns:
            df_consolidado['Ano'] = pd.to_datetime(
                df_consolidado['Data'], 
                dayfirst=True, 
                errors='coerce'
            ).dt.year
        
        # Limpar espaços em branco
        if 'Responsavel' in df_consolidado.columns:
            df_consolidado['Responsavel'] = df_consolidado['Responsavel'].str.strip()
        
        return df_consolidado
        
    except Exception as e:
        st.error(f"Erro ao processar dados: {str(e)}")
        return pd.DataFrame()

def obter_setores_permitidos(nome_usuario: str) -> List[str]:
    """
    Obtém os setores permitidos para um usuário.
    
    Args:
        nome_usuario: Nome do usuário
        
    Returns:
        Lista de setores permitidos
    """
    return SETORES_POR_USUARIO.get(nome_usuario, ["SPN", "ITI"])

def gerar_titulo_dinamico(titulo_base: str, setores_selecionados: List[str]) -> str:
    """
    Gera título dinâmico baseado nos setores selecionados.
    
    Args:
        titulo_base: Título base
        setores_selecionados: Lista de setores selecionados
        
    Returns:
        Título formatado com HTML
    """
    # Normalizar seleção: remover duplicados, espaços e manter maiúsculas
    setores_norm = [str(s).strip().upper() for s in setores_selecionados if s]
    setores_unicos = list(dict.fromkeys(setores_norm))  # preserva ordem
    setores_set = set(setores_unicos)

    if len(setores_set) == 0:
        return titulo_base
    if len(setores_set) == 1:
        unico = setores_unicos[0]
        if unico == "SPN":
            return f"{titulo_base} - <span style='color: {COLORS['primary']};'>SPN</span>"
        if unico == "ITI":
            return f"{titulo_base} - <span style='color: {COLORS['secondary']};'>ITI</span>"
        # Qualquer outro valor único
        return f"{titulo_base} - <span style='color: {COLORS['neutral']};'>{unico}</span>"
    # Dois ou mais filtros selecionados: título Consolidado
    return f"{titulo_base} - <span style='color: {COLORS['success']};'>Consolidado</span>"

# ==================== FUNÇÕES DE GRÁFICOS ====================

def criar_grafico_comparativo(df_filtrado: pd.DataFrame) -> go.Figure:
    """
    Cria gráfico comparativo entre Total, Resolvidos e Pendentes por setor.
    
    Args:
        df_filtrado: DataFrame filtrado
        
    Returns:
        Figura do Plotly
    """
    # Calcular totais por setor
    df_total_sector = df_filtrado['Setor'].value_counts()
    df_resolved = df_filtrado[df_filtrado['Status'] == 'Resolvido']
    df_resolved_sector = df_resolved['Setor'].value_counts()
    df_unresolved_sector = df_total_sector - df_resolved_sector.reindex(
        df_total_sector.index, fill_value=0
    )
    
    # Criar figura
    fig = go.Figure()
    
    # Adicionar barras com gradiente e sombra
    traces = [
        ('Pendentes', df_unresolved_sector, COLORS['pending']),
        ('Resolvidos', df_resolved_sector.reindex(df_total_sector.index, fill_value=0), COLORS['resolved']),
        ('Total', df_total_sector, COLORS['total'])
    ]
    
    for name, data, color in traces:
        fig.add_trace(go.Bar(
            x=data.index,
            y=data.values,
            name=name,
            marker=dict(
                color=color,
                line=dict(color='rgba(0,0,0,0.1)', width=1),
                opacity=0.8
            ),
            text=[f'<b>{val}</b><br>({(val / df_total_sector.sum() * 100):.1f}%)' 
                  for val in data.values],
            textposition='inside',
            textfont=dict(size=12, color='white', family='Arial Black'),
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Setor: %{x}<br>' +
                         'Quantidade: %{y}<br>' +
                         '<extra></extra>'
        ))
    
    # Configurar layout simplificado para compatibilidade com Streamlit Cloud
    try:
        fig.update_layout(
            title='Comparativo por Setor - Visão Geral',
            xaxis_title='Setor',
            yaxis_title='Quantidade de Registros',
            barmode='group',
            bargap=0.15,
            bargroupgap=0.1,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1
            ),
            height=500,
            showlegend=True
        )
        
        # Aplicar rotação dos labels do eixo X separadamente
        fig.update_xaxes(tickangle=-45)
        
    except Exception as e:
        # Fallback para layout básico em caso de erro
        fig.update_layout(
            title='Comparativo por Setor - Visão Geral',
            barmode='group',
            height=500
        )
    
    return fig

def criar_grafico_backlog_status(df_filtrado: pd.DataFrame) -> Optional[go.Figure]:
    """
    Cria gráfico de evolução do backlog por status.
    
    Args:
        df_filtrado: DataFrame filtrado
        
    Returns:
        Figura do Plotly ou None se não houver dados
    """
    if 'Backlog' not in df_filtrado.columns:
        return None
    
    try:
        # Processar dados de backlog
        df_temp = df_filtrado.copy()
        df_temp['Backlog'] = pd.to_datetime(df_temp['Backlog'], format='%m/%Y')
        
        backlog_por_status = (
            df_temp.groupby(['Backlog', 'Status'])
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )
        
        backlog_por_status = backlog_por_status.sort_values(by='Backlog')
        backlog_por_status['Backlog_str'] = backlog_por_status['Backlog'].dt.strftime('%b/%Y')
        
        # Criar gráfico de linha moderno
        fig = go.Figure()
        
        # Adicionar linha para Resolvidos
        if 'Resolvido' in backlog_por_status.columns:
            fig.add_trace(go.Scatter(
                x=backlog_por_status['Backlog'],
                y=backlog_por_status['Resolvido'],
                mode='lines+markers+text',
                name='Resolvidos',
                line=dict(color=COLORS['resolved'], width=4, shape='spline'),
                marker=dict(size=8, color=COLORS['resolved'], 
                           line=dict(width=2, color='white')),
                text=backlog_por_status['Resolvido'],
                textposition='top center',
                textfont=dict(size=11, color=COLORS['resolved'], family='Arial Black'),
                fill='tonexty',
                fillcolor=f"rgba({int(COLORS['resolved'][1:3], 16)}, {int(COLORS['resolved'][3:5], 16)}, {int(COLORS['resolved'][5:7], 16)}, 0.1)",
                hovertemplate='<b>Resolvidos</b><br>Período: %{x}<br>Quantidade: %{y}<extra></extra>'
            ))
        
        # Adicionar linha para Pendentes
        if 'Pendente' in backlog_por_status.columns:
            fig.add_trace(go.Scatter(
                x=backlog_por_status['Backlog'],
                y=backlog_por_status['Pendente'],
                mode='lines+markers+text',
                name='Pendentes',
                line=dict(color=COLORS['pending'], width=4, shape='spline'),
                marker=dict(size=8, color=COLORS['pending'],
                           line=dict(width=2, color='white')),
                text=backlog_por_status['Pendente'],
                textposition='bottom center',
                textfont=dict(size=11, color=COLORS['pending'], family='Arial Black'),
                hovertemplate='<b>Pendentes</b><br>Período: %{x}<br>Quantidade: %{y}<extra></extra>'
            ))
        
        # Adicionar linha de média se houver dados resolvidos
        if 'Resolvido' in backlog_por_status.columns:
            media_resolvidos = backlog_por_status['Resolvido'].mean()
            fig.add_hline(
                y=media_resolvidos,
                line_dash="dash",
                line_color=COLORS['neutral'],
                line_width=2,
                annotation_text=f"<b>Média Resolvidos: {media_resolvidos:.1f}</b>",
                annotation_position="top left",
                annotation_font=dict(size=12, color=COLORS['text'])
            )
        
        # Configurar layout simplificado para compatibilidade com Streamlit Cloud
        try:
            fig.update_layout(
                title='Evolução Temporal do Backlog',
                xaxis_title='Período (Mês/Ano)',
                yaxis_title='Quantidade de Registros',
                height=500
            )
            
            # Eixo temporal com seletor de período (sem mini-gráfico duplicado)
            fig.update_xaxes(
                type='date',
                tickformat='%b/%Y',
                rangeselector=dict(
                    buttons=list([
                        dict(count=3, label='3m', step='month', stepmode='backward'),
                        dict(count=6, label='6m', step='month', stepmode='backward'),
                        dict(count=1, label='1y', step='year', stepmode='backward'),
                        dict(step='all', label='Tudo')
                    ])
                ),
                rangeslider=dict(visible=False)
            )
            
        except Exception as layout_error:
            # Fallback para layout básico
            fig.update_layout(
                title='Evolução Temporal do Backlog',
                height=500
            )
        
        return fig
        
    except Exception as e:
        st.error(f"Erro ao criar gráfico de backlog: {str(e)}")
        return None

def criar_grafico_pizza_responsaveis(df_filtrado: pd.DataFrame) -> Optional[go.Figure]:
    """
    Cria gráfico de pizza da distribuição por responsáveis.
    
    Args:
        df_filtrado: DataFrame filtrado
        
    Returns:
        Figura do Plotly ou None se não houver dados
    """
    if 'Responsavel' not in df_filtrado.columns:
        return None
    
    try:
        # Processar dados
        df_status = (
            df_filtrado
            .drop_duplicates(subset=['Responsavel', 'Incidente'])
            .groupby('Responsavel')
            .size()
        )
        
        # Top N (8) estrito e agrupamento "Outros"
        top_n_series = df_status.nlargest(TOP_N_RESPONSAVEIS).astype(int)
        restante_sum = int(df_status.sum() - int(top_n_series.sum()))
        if restante_sum > 0:
            df_status_pizza = pd.concat([
                top_n_series,
                pd.Series([restante_sum], index=['Outros'])
            ])
        else:
            df_status_pizza = top_n_series
        
        if df_status_pizza.empty:
            return None
        
        # Criar paleta de cores dinâmica
        colors_palette = [
            COLORS['primary'], COLORS['secondary'], COLORS['success'], 
            COLORS['pending'], COLORS['resolved'], COLORS['total'],
            COLORS['neutral'], '#E74C3C', '#9B59B6', '#F39C12'
        ]
        
        # Criar gráfico de pizza moderno
        fig = go.Figure(data=[go.Pie(
            labels=df_status_pizza.index,
            values=df_status_pizza.values,
            hole=0.4,
            marker=dict(
                colors=colors_palette[:len(df_status_pizza)],
                line=dict(color='white', width=3)
            ),
            textinfo='label+percent+value',
            textposition='auto',
            textfont=dict(size=12, color='white', family='Arial Black'),
            hovertemplate='<b>%{label}</b><br>' +
                         'Registros: %{value}<br>' +
                         'Percentual: %{percent}<br>' +
                         '<extra></extra>',
            pull=[0.05 if i == 0 else 0 for i in range(len(df_status_pizza))]
        )])
        
        # Configurar layout simplificado para compatibilidade com Streamlit Cloud
        try:
            # Título dinâmico por setor, quando houver apenas um setor
            titulo = 'Distribuição por Responsáveis'
            if 'Setor' in df_filtrado.columns:
                setores_unicos = df_filtrado['Setor'].dropna().unique()
                if len(setores_unicos) == 1:
                    titulo = f"{titulo} — {setores_unicos[0]}"

            fig.update_layout(title=titulo, height=500)
            
            # Adicionar anotação central separadamente
            fig.add_annotation(
                text=f"Total<br>{df_status_pizza.sum()}",
                x=0.5, y=0.5,
                font_size=16,
                showarrow=False
            )
            
        except Exception as layout_error:
            # Fallback para layout básico
            fig.update_layout(title='Distribuição por Responsáveis', height=500)
        
        return fig
        
    except Exception as e:
        st.error(f"Erro ao criar gráfico de responsáveis: {str(e)}")
        return None

def criar_grafico_desempenho(df_filtrado: pd.DataFrame) -> go.Figure:
    """
    Cria gráfico de desempenho dos responsáveis.
    
    Args:
        df_filtrado: DataFrame filtrado
        
    Returns:
        Figura do Plotly
    """
    fig = go.Figure()
    
    if 'Responsavel' not in df_filtrado.columns:
        return fig
    
    try:
        # Processar dados de responsáveis
        df_responsavel_grouped = (
            df_filtrado
            .drop_duplicates(subset=['Responsavel', 'Incidente'])
            .groupby(['Responsavel', 'Status'])
            .size()
            .unstack(fill_value=0)
        )
        
        df_responsavel_grouped['Total'] = df_responsavel_grouped.sum(axis=1)
        resolvidos_series = (
            df_responsavel_grouped['Resolvido']
            if 'Resolvido' in df_responsavel_grouped.columns
            else pd.Series(0, index=df_responsavel_grouped.index)
        )
        df_responsavel_grouped['Percentual_Resolvidos'] = (
            resolvidos_series / df_responsavel_grouped['Total']
        ) * 100
        
        df_responsavel_grouped = df_responsavel_grouped.reset_index()

        # Agrupar responsáveis com Total <= 6 em "Outros" e ordenar do maior para o menor
        limiar_outros = 6
        df_main = df_responsavel_grouped[df_responsavel_grouped['Total'] > limiar_outros].copy()
        df_small = df_responsavel_grouped[df_responsavel_grouped['Total'] <= limiar_outros].copy()
        if not df_small.empty:
            resolvido_sum = int(df_small.get('Resolvido', 0).sum()) if 'Resolvido' in df_small.columns else 0
            pendente_sum = int(df_small.get('Pendente', 0).sum()) if 'Pendente' in df_small.columns else 0
            total_sum = int(df_small['Total'].sum())
            outros_pct = (resolvido_sum / total_sum * 100) if total_sum > 0 else 0
            df_main = pd.concat([
                df_main,
                pd.DataFrame([{
                    'Responsavel': 'Outros',
                    'Resolvido': resolvido_sum,
                    'Pendente': pendente_sum,
                    'Total': total_sum,
                    'Percentual_Resolvidos': outros_pct
                }])
            ], ignore_index=True)

        # Selecionar Top 10 após ordenação (inclui "Outros" se estiver entre os 10 maiores)
        df_responsavel_maior5 = df_main.sort_values(by='Total', ascending=False).head(10)
        
        # Adicionar barras com estilo moderno
        traces = [
            ('Pendentes', 'Pendente', COLORS['pending']),
            ('Resolvidos', 'Resolvido', COLORS['resolved'])
        ]
        
        for name, column, color in traces:
            serie_vals = (
                df_responsavel_maior5[column]
                if column in df_responsavel_maior5.columns
                else pd.Series(0, index=df_responsavel_maior5.index)
            )
            fig.add_trace(go.Bar(
                orientation='h',
                x=serie_vals,
                y=df_responsavel_maior5['Responsavel'],
                name=name,
                marker=dict(
                    color=color,
                    line=dict(color='white', width=2),
                    pattern_fillmode='overlay'
                ),
                text=serie_vals,
                textposition='outside',
                textfont=dict(size=12, color=COLORS['text'], family='Arial Black'),
                cliponaxis=False,
                hovertemplate=f'<b>{name}</b><br>' +
                             'Responsável: %{y}<br>' +
                             'Quantidade: %{x}<br>' +
                             '<extra></extra>'
            ))

        # Anotações de percentual com barras horizontais
        for i in range(len(df_responsavel_maior5)):
            fig.add_annotation(
                xref='paper', yref='y',
                x=1.02,
                y=df_responsavel_maior5['Responsavel'].iloc[i],
                text=f"<b>{df_responsavel_maior5['Percentual_Resolvidos'].iloc[i]:.1f}%</b>",
                showarrow=False,
                font=dict(size=12, color=COLORS['text'], family='Arial Black'),
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor=COLORS['text'],
                borderwidth=1
            )

        # Configurar layout simplificado para compatibilidade com Streamlit Cloud
        try:
            # Título dinâmico com setor quando houver apenas um e indicação de Top 10
            titulo = 'Desempenho Individual dos Responsáveis'
            if 'Setor' in df_filtrado.columns:
                setores_unicos = df_filtrado['Setor'].dropna().unique()
                if len(setores_unicos) == 1:
                    titulo = f"{titulo} — {setores_unicos[0]}"
            # Acrescentar indicação de Top 10
            titulo = f"{titulo} — Top 10"
            # Altura dinâmica para suportar muitos itens (evita agrupamento em "Outros")
            bar_height_px = 28
            base_padding_px = 120
            dynamic_height = max(500, bar_height_px * len(df_responsavel_maior5) + base_padding_px)

            fig.update_layout(
                title=titulo,
                xaxis_title='Quantidade de Registros',
                yaxis_title='Responsável',
                barmode='stack',
                height=dynamic_height,
                yaxis=dict(automargin=True),
                margin=dict(r=120)
            )
            # Inverter o eixo Y para mostrar do maior para o menor de cima para baixo
            fig.update_yaxes(autorange='reversed')
            
        except Exception as layout_error:
            # Fallback para layout básico
            fig.update_layout(
                title='Desempenho Individual dos Responsáveis',
                height=500
            )
        
        return fig
        
    except Exception as e:
        st.error(f"Erro ao criar gráfico de desempenho: {str(e)}")
        return fig

# ==================== ESTILOS CSS APRIMORADOS ====================

def aplicar_estilos_css() -> None:
    """Aplica estilos CSS personalizados para um visual limpo e claro."""
    st.markdown("""
        <style>
        /* Estilo geral da aplicação */
        .main {
            background-color: #fafafa;
            font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        /* Removido padding-top que causava espaços vazios */
        
        /* Sidebar personalizada */
        .css-1d391kg {
            background-color: #ffffff;
            border-right: 2px solid #e9ecef;
        }
        
        /* Métricas - Removidos os estilos dos cards brancos desnecessários */
        
        /* Tabelas */
        .stDataFrame {
            background-color: #ffffff;
            border-radius: 8px;
            border: 1px solid #e9ecef;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .stDataFrame td, .stDataFrame th {
            text-align: center !important;
            vertical-align: middle !important;
            padding: 12px 8px !important;
            border-bottom: 1px solid #f1f3f4 !important;
        }
        
        .stDataFrame th {
            background-color: #f8f9fa !important;
            font-weight: 600 !important;
            color: #495057 !important;
        }
        
        /* Botões */
        .stButton > button {
            background: linear-gradient(90deg, #007bff 0%, #0056b3 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            background: linear-gradient(90deg, #0056b3 0%, #004085 100%);
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,123,255,0.3);
        }
        
        /* Filtros */
        .stMultiSelect > div > div {
            background-color: #ffffff;
            border: 2px solid #e9ecef;
            border-radius: 8px;
        }
        
        /* Títulos */
        h1, h2, h3 {
            color: #2c3e50;
            font-weight: 600;
        }
        
        /* Gráficos */
        .js-plotly-plot {
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: 1px solid #e9ecef;
            background-color: #ffffff;
        }
        /* Container com rolagem para gráficos altos */
        .chart-scroll {
            max-height: 600px;
            overflow-y: auto;
            padding-right: 8px; /* espaço para barra de rolagem */
        }
        
        /* CSS da classe .login removido - card branco desnecessário eliminado */
        
        /* Alertas */
        .stAlert {
            border-radius: 8px;
            border: none;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 4px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            border-radius: 6px;
            color: #6c757d;
            font-weight: 500;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #ffffff !important;
            color: #2c3e50 !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Responsividade */
        @media (max-width: 768px) {
            .fixed-header {
                flex-direction: column;
                text-align: center;
                padding: 10px;
            }
            
            .fixed-header h1 {
                font-size: 24px;
            }
            
            .fixed-header h2 {
                font-size: 16px;
            }
        }
        </style>
    """, unsafe_allow_html=True)

# ==================== FUNÇÕES DE INTERFACE ====================

def renderizar_tela_login() -> None:
    """Renderiza a tela de login."""
    st.markdown('<h1 style="text-align: center; color: #2c3e50; margin-bottom: 30px; font-size: 32px; font-weight: 700;">DataPaws</h1>', unsafe_allow_html=True)

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
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")

def renderizar_cabecalho() -> None:
    """Renderiza o cabeçalho da aplicação."""
    # Seção de usuário com estilo melhorado
    st.sidebar.markdown(
        f"""
        <div style='background-color: #f0f2f6; padding: 12px; border-radius: 8px; margin-bottom: 15px;'>
            <div style='display: flex; align-items: center;'>
                <div style='background-color: #2E86AB; color: white; border-radius: 50%; width: 36px; height: 36px; 
                    display: flex; align-items: center; justify-content: center; margin-right: 10px; font-size: 16px;'>
                    {st.session_state.nome_usuario[0].upper()}
                </div>
                <div>
                    <div style='font-weight: 600; color: #2c3e50;'>Bem-vindo</div>
                    <div style='font-size: 14px; color: #6c757d;'>{st.session_state.nome_usuario}</div>
                </div>
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )

    # Botão de logout com estilo melhorado
    if st.sidebar.button("📤 Logout", use_container_width=True):
        st.session_state.login = False
        st.success("Logout realizado com sucesso!")
        st.rerun()
    
    # Separador para a seção de filtros - AGORA PRIMEIRO
    st.sidebar.markdown("""
        <div style='margin: 20px 0 10px 0;'>
            <div style='font-size: 12px; font-weight: 600; color: #6c757d; text-transform: uppercase; letter-spacing: 1px;'>
                FILTROS
            </div>
            <hr style='margin: 5px 0 15px 0; border: none; height: 1px; background-color: #e9ecef;'>
        </div>
    """, unsafe_allow_html=True)
    
    # Renderizar o filtro de setores logo após o título FILTROS
    usuario_nome = st.session_state.nome_usuario
    setores_permitidos = obter_setores_permitidos(usuario_nome)
    
    # Inicializar df_consolidado se não existir
    if 'df_consolidado' not in st.session_state:
        try:
            # Carregar dados para garantir que temos setores disponíveis
            df_consolidado = carregar_dados()
            st.session_state.df_consolidado = df_consolidado
        except Exception as e:
            # Em caso de erro, criar um DataFrame vazio com a coluna 'Setor'
            df_consolidado = pd.DataFrame({'Setor': ['SPN', 'ITI']})
            st.session_state.df_consolidado = df_consolidado
            st.warning(f"Não foi possível carregar os dados. Usando setores padrão.")
    else:
        df_consolidado = st.session_state.df_consolidado
    
    # Filtrar setores disponíveis
    setores_disponiveis = [
        s for s in df_consolidado['Setor'].unique() 
        if s in setores_permitidos
    ]
    
    # Filtro de setores removido conforme solicitado: visão consolidada no Dashboard
    # Controles rápidos já removidos
    
    # Separador com título da seção - AGORA DEPOIS DOS FILTROS
    st.sidebar.markdown("""
        <div style='margin: 20px 0 10px 0;'>
            <div style='font-size: 12px; font-weight: 600; color: #6c757d; text-transform: uppercase; letter-spacing: 1px;'>
                INFORMAÇÕES DO SISTEMA
            </div>
            <hr style='margin: 5px 0 15px 0; border: none; height: 1px; background-color: #e9ecef;'>
        </div>
    """, unsafe_allow_html=True)
    
    # Informações de governança de TI com estilo melhorado
    st.sidebar.markdown(
        """
        <div style='padding: 12px; background-color: #f8f9fa; border-radius: 8px; border-left: 4px solid #2E86AB; margin-bottom: 15px;'>
            <h4 style='color: #2c3e50; margin: 0 0 8px 0; font-size: 15px; display: flex; align-items: center;'>
                <span style='margin-right: 8px;'>📊</span> Dashboard de Backlog TI
            </h4>
            <p style='color: #6c757d; margin: 0 0 10px 0; font-size: 13px; line-height: 1.4;'>
                Sistema de análise e monitoramento do backlog de tickets dos setores ITI e SPN.
            </p>
            <div style='background-color: rgba(46, 134, 171, 0.1); padding: 8px; border-radius: 4px;'>
                <p style='color: #6c757d; margin: 0; font-size: 12px;'>
                    <strong>Desenvolvido por:</strong> Governança de TI<br>
                    <strong>Finalidade:</strong> Gestão e controle do backlog
                </p>
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Explicação sobre o conceito de backlog com estilo melhorado
    st.sidebar.markdown(
        """
        <div style='padding: 12px; background-color: #f8f9fa; border-radius: 8px; border-left: 4px solid #F18F01; margin-bottom: 15px;'>
            <h4 style='color: #2c3e50; margin: 0 0 8px 0; font-size: 15px; display: flex; align-items: center;'>
                <span style='margin-right: 8px;'>💡</span> O que é Backlog?
            </h4>
            <p style='color: #6c757d; margin: 0 0 10px 0; font-size: 13px; line-height: 1.5;'>
                Backlog representa os tickets que não foram atendidos dentro do SLA (Service Level Agreement) estabelecido. 
                São chamados que ultrapassaram o tempo acordado para resolução e precisam de atenção prioritária.
            </p>
            <div style='background-color: rgba(241, 143, 1, 0.1); padding: 8px; border-radius: 4px;'>
                <p style='color: #6c757d; margin: 0; font-size: 12px;'>
                    <strong>Importância:</strong> Monitorar o backlog permite identificar gargalos operacionais, 
                    redistribuir recursos e priorizar chamados críticos para reduzir o tempo de espera dos usuários.
                </p>
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Fim da função renderizar_cabecalho

@st.cache_data(ttl=300)  # Cache por 5 minutos
def processar_metricas_dashboard(df_filtrado: pd.DataFrame) -> Dict[str, int]:
    """
    Processa métricas do dashboard com cache.
    
    Args:
        df_filtrado: DataFrame filtrado
        
    Returns:
        Dicionário com métricas calculadas
    """
    if df_filtrado.empty:
        return {'total': 0, 'resolvidos': 0, 'pendentes': 0}
    
    status_counts = df_filtrado['Status'].value_counts()
    return {
        'total': len(df_filtrado),
        'resolvidos': status_counts.get('Resolvido', 0),
        'pendentes': status_counts.get('Pendente', 0)
    }

def renderizar_metricas_resumo(df_filtrado: pd.DataFrame) -> None:
    """
    Renderiza as métricas de resumo do dashboard.
    
    Args:
        df_filtrado: DataFrame filtrado
    """
    if df_filtrado.empty:
        st.warning("Nenhum registro encontrado com os filtros aplicados.")
        return
    
    # Usar função otimizada com cache
    metricas = processar_metricas_dashboard(df_filtrado)
    
    # Calcular percentuais
    total_registros = metricas['total']
    total_resolvidos = metricas['resolvidos']
    total_pendentes = metricas['pendentes']
    
    percentual_resolvidos = (total_resolvidos / total_registros * 100) if total_registros > 0 else 0
    percentual_pendentes = (total_pendentes / total_registros * 100) if total_registros > 0 else 0
    
    # Exibir métricas sem containers (removidos os cards brancos desnecessários)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Total de Registros",
            value=total_registros
        )
    
    with col2:
        st.metric(
            label="Resolvidos",
            value=f"{total_resolvidos} ({percentual_resolvidos:.1f}%)"
        )
    
    with col3:
        st.metric(
            label="Pendentes",
            value=f"{total_pendentes} ({percentual_pendentes:.1f}%)"
        )

def renderizar_dashboard(df_consolidado: pd.DataFrame) -> None:
    """
    Renderiza a aba do dashboard.
    
    Args:
        df_consolidado: DataFrame consolidado
    """
    # Salvar o DataFrame consolidado no session_state para uso no cabeçalho
    st.session_state.df_consolidado = df_consolidado
    
    # Obter setores permitidos para o usuário
    usuario_nome = st.session_state.nome_usuario
    setores_permitidos = obter_setores_permitidos(usuario_nome)
    setores_disponiveis = [
        s for s in df_consolidado['Setor'].unique() 
        if s in setores_permitidos
    ]

    # Visão consolidada: considerar sempre todos os setores disponíveis
    setores_selecionados = setores_disponiveis

    # Título dinâmico
    titulo = gerar_titulo_dinamico("Visão Geral do Backlog", setores_selecionados)
    st.markdown(f"<h1>{titulo}</h1>", unsafe_allow_html=True)
    # Última atualização do arquivo consolidado
    try:
        mtime = os.path.getmtime(APP_CONFIG['data_file'])
        st.caption(f"Atualizado em {datetime.fromtimestamp(mtime).strftime('%d/%m/%Y %H:%M')}")
    except Exception:
        pass

    # Aplicar filtros
    df_filtrado = df_consolidado[df_consolidado['Setor'].isin(setores_selecionados)]
    
    # Renderizar métricas
    renderizar_metricas_resumo(df_filtrado)
    
    if df_filtrado.empty:
        return
    
    # Criar e exibir gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        fig_comparativo = criar_grafico_comparativo(df_filtrado)
        st.plotly_chart(fig_comparativo, use_container_width=True)
    
    with col2:
        fig_backlog = criar_grafico_backlog_status(df_filtrado)
        if fig_backlog:
            st.plotly_chart(fig_backlog, use_container_width=True)
    
    col3, col4 = st.columns(2)

    # Gráficos inferiores por setor: barras horizontais para ITI e SPN
    with col3:
        df_iti = df_filtrado[df_filtrado['Setor'] == 'ITI']
        fig_desempenho_iti = criar_grafico_desempenho(df_iti)
        st.markdown("<div class='chart-scroll'>", unsafe_allow_html=True)
        st.plotly_chart(fig_desempenho_iti, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col4:
        df_spn = df_filtrado[df_filtrado['Setor'] == 'SPN']
        fig_desempenho_spn = criar_grafico_desempenho(df_spn)
        st.markdown("<div class='chart-scroll'>", unsafe_allow_html=True)
        st.plotly_chart(fig_desempenho_spn, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Exportar recorte atual
    try:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_filtrado.to_excel(writer, index=False, sheet_name='Backlog')
        buffer.seek(0)
        st.download_button(
            label='⬇️ Exportar recorte para Excel',
            data=buffer,
            file_name='Backlog_Detalhado.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception:
        # Silenciar aviso de exportação para evitar barra amarela
        pass

def renderizar_relatorios(df_consolidado: pd.DataFrame) -> None:
    """
    Renderiza a aba de relatórios.
    
    Args:
        df_consolidado: DataFrame consolidado
    """
    # Segmentação por usuário
    usuario_nome = st.session_state.nome_usuario
    setores_permitidos = obter_setores_permitidos(usuario_nome)
    df_consolidado_relatorio = df_consolidado[
        df_consolidado['Setor'].isin(setores_permitidos)
    ]

    # Inicializar filtros no session_state
    filtros_default = {
        "filtro_relatorio_setor": list(df_consolidado_relatorio['Setor'].unique()),
        "filtro_relatorio_status": ["Resolvido", "Pendente"],
        "filtro_relatorio_responsavel": ["Todos"],
        "filtro_relatorio_colunas": ["Todos"]
    }
    
    for key, default_value in filtros_default.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

    # Título dinâmico
    setor_filtro = st.session_state["filtro_relatorio_setor"]
    titulo = gerar_titulo_dinamico("Consulta Detalhada do Backlog", setor_filtro)
    st.markdown(f"<h1>{titulo}</h1>", unsafe_allow_html=True)

    # Filtros do Relatório
    st.markdown("### Filtros do Relatório")
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

    with col1:
        setor_filtro = st.multiselect(
            "Setor", 
            df_consolidado_relatorio['Setor'].unique(),
            key="filtro_relatorio_setor"
        )

    with col2:
        responsaveis_disponiveis = sorted(
            df_consolidado_relatorio[
                df_consolidado_relatorio['Setor'].isin(setor_filtro)
            ]['Responsavel'].unique()
        )
        opcoes_responsavel = ["Todos"] + responsaveis_disponiveis
        responsavel_filtro = st.multiselect(
            "Responsável", 
            opcoes_responsavel,
            key="filtro_relatorio_responsavel"
        )
        
        responsaveis_filtrados = (
            responsaveis_disponiveis 
            if "Todos" in responsavel_filtro or not responsavel_filtro 
            else responsavel_filtro
        )

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

    # Aplicar filtros
    df_relatorio = df_consolidado_relatorio[
        (df_consolidado_relatorio['Setor'].isin(setor_filtro)) &
        (df_consolidado_relatorio['Status'].isin(
            st.session_state.get("filtro_relatorio_status", [])
        )) &
        (df_consolidado_relatorio['Responsavel'].isin(responsaveis_filtrados))
    ].copy()

    # Corrigir formatação de colunas numéricas
    for col in ['Ano', 'Incidente']:
        if col in df_relatorio.columns and pd.api.types.is_numeric_dtype(df_relatorio[col]):
            df_relatorio[col] = df_relatorio[col].astype(str).str.replace(',', '')

    # CSS para centralizar tabela
    st.markdown("""
        <style>
        .stDataFrame td, .stDataFrame th {
            text-align: center !important;
            vertical-align: middle !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Botão de exportação e contador
    col5, col6 = st.columns([0.8, 0.2])
    
    with col5:
        st.write(f"**Total de registros encontrados:** {len(df_relatorio)}")
    
    with col6:
        if not df_relatorio.empty:
            excel_buffer = io.BytesIO()
            df_relatorio[colunas_exibir].to_excel(excel_buffer, index=False)
            st.download_button(
                label="Exportar para Excel",
                data=excel_buffer.getvalue(),
                file_name='Backlog_Detalhado.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                use_container_width=True,
            )

    # Exibir relatório
    if not df_relatorio.empty:
        st.dataframe(df_relatorio[colunas_exibir], use_container_width=True, height=700)
    else:
        st.warning("Nenhum registro encontrado com os filtros aplicados.")

# ==================== FUNÇÃO PRINCIPAL ====================

def main() -> None:
    """Função principal da aplicação."""
    # Configurar página
    configurar_pagina()
    
    # Aplicar estilos CSS aprimorados
    aplicar_estilos_css()
    
    # Inicializar estado de login
    if 'login' not in st.session_state:
        st.session_state.login = False

    # Verificar se está logado
    if not st.session_state.login:
        renderizar_tela_login()
        return

    # Renderizar aplicação principal
    renderizar_cabecalho()
    
    # Carregar e processar dados
    df_dados = carregar_dados(APP_CONFIG['data_file'])
    if not df_dados:
        st.error("Não foi possível carregar os dados.")
        return
    
    df_consolidado = processar_dados_consolidados(df_dados)
    if df_consolidado.empty:
        st.error("Não foi possível processar os dados.")
        return

    # Renderizar abas
    if MINIMAL_MODE:
        # Somente o que é usado: mostrar apenas o Dashboard
        renderizar_dashboard(df_consolidado)
    else:
        abas = st.tabs(["Dashboard", "Relatórios"])
        with abas[0]:
            renderizar_dashboard(df_consolidado)
        with abas[1]:
            renderizar_relatorios(df_consolidado)

if __name__ == "__main__":
    main()

# ==================== OTIMIZAÇÕES DE PERFORMANCE ====================



@st.cache_data(ttl=300)
def processar_dados_graficos(df_filtrado: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Processa dados para gráficos com cache.
    
    Args:
        df_filtrado: DataFrame filtrado
        
    Returns:
        Dicionário com dados processados para gráficos
    """
    resultado = {}
    
    # Dados para gráfico comparativo
    if not df_filtrado.empty:
        df_total_sector = df_filtrado['Setor'].value_counts()
        df_resolved = df_filtrado[df_filtrado['Status'] == 'Resolvido']
        df_resolved_sector = df_resolved['Setor'].value_counts()
        df_unresolved_sector = df_total_sector - df_resolved_sector.reindex(
            df_total_sector.index, fill_value=0
        )
        
        resultado['comparativo'] = {
            'total': df_total_sector,
            'resolvidos': df_resolved_sector,
            'pendentes': df_unresolved_sector
        }
    
    # Dados para gráfico de responsáveis
    if 'Responsavel' in df_filtrado.columns and not df_filtrado.empty:
        df_status = (
            df_filtrado
            .drop_duplicates(subset=['Responsavel', 'Incidente'])
            .groupby('Responsavel')
            .size()
        )
        resultado['responsaveis'] = df_status
    
    return resultado

# ==================== ESTILOS CSS APRIMORADOS ====================

def aplicar_estilos_css() -> None:
    """Aplica estilos CSS personalizados para um visual limpo e claro."""
    st.markdown("""
        <style>
        /* Estilo geral da aplicação */
        .main {
            background-color: #fafafa;
            font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        /* Cabeçalho fixo */
        .fixed-header {
            position: fixed; 
            top: 0; 
            left: 0; 
            right: 0; 
            background: linear-gradient(90deg, #ffffff 0%, #f8f9fa 100%);
            z-index: 1000; 
            border-bottom: 2px solid #e9ecef; 
            padding: 15px 20px; 
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        } 
        
        .fixed-header h1 {
            margin: 0; 
            font-size: 28px;
            color: #2c3e50;
            font-weight: 600;
        } 
        
        .fixed-header h2 {
            margin: 0; 
            font-size: 18px; 
            color: #6c757d;
            font-weight: 400;
        }
        
        /* Sidebar personalizada */
        .css-1d391kg {
            background-color: #ffffff;
            border-right: 2px solid #e9ecef;
        }
        
        /* Métricas - Removida duplicação dos estilos dos cards brancos */
        
        /* Tabelas */
        .stDataFrame {
            background-color: #ffffff;
            border-radius: 8px;
            border: 1px solid #e9ecef;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .stDataFrame td, .stDataFrame th {
            text-align: center !important;
            vertical-align: middle !important;
            padding: 12px 8px !important;
            border-bottom: 1px solid #f1f3f4 !important;
        }
        
        .stDataFrame th {
            background-color: #f8f9fa !important;
            font-weight: 600 !important;
            color: #495057 !important;
        }
        
        /* Botões */
        .stButton > button {
            background: linear-gradient(90deg, #007bff 0%, #0056b3 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            background: linear-gradient(90deg, #0056b3 0%, #004085 100%);
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,123,255,0.3);
        }
        
        /* Filtros */
        .stMultiSelect > div > div {
            background-color: #ffffff;
            border: 2px solid #e9ecef;
            border-radius: 8px;
        }
        
        /* Títulos */
        h1, h2, h3 {
            color: #2c3e50;
            font-weight: 600;
        }
        
        /* Gráficos */
        .js-plotly-plot {
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: 1px solid #e9ecef;
            background-color: #ffffff;
        }
        
        /* Login */
        .login {
            max-width: 400px;
            margin: 0 auto;
            padding: 40px 20px;
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border-radius: 16px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.1);
            border: 1px solid #e9ecef;
        }
        
        .login h1 {
            text-align: center;
            color: #2c3e50;
            margin-bottom: 30px;
            font-size: 32px;
            font-weight: 700;
        }
        
        /* Alertas */
        .stAlert {
            border-radius: 8px;
            border: none;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 4px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            border-radius: 6px;
            color: #6c757d;
            font-weight: 500;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #ffffff !important;
            color: #2c3e50 !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Responsividade */
        @media (max-width: 768px) {
            .fixed-header {
                flex-direction: column;
                text-align: center;
                padding: 10px;
            }
            
            .fixed-header h1 {
                font-size: 24px;
            }
            
            .fixed-header h2 {
                font-size: 16px;
            }
        }
        </style>
    """, unsafe_allow_html=True)
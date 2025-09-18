"""
DataPaws - Dashboard de Análise de Backlog
Aplicação Streamlit para análise de dados consolidados de backlog
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

# Configurações da aplicação
APP_CONFIG = {
    'title': 'DataPaws',
    'icon': 'Base/IMG/Designer.jpeg',
    'data_file': 'Base/consolidado.xlsx'
}

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
    if setores_selecionados == ["SPN"]:
        return f"{titulo_base} - <span style='color: {COLORS['primary']};'>SPN</span>"
    elif setores_selecionados == ["ITI"]:
        return f"{titulo_base} - <span style='color: {COLORS['secondary']};'>ITI</span>"
    elif set(setores_selecionados) == {"SPN", "ITI"}:
        return f"{titulo_base} - <span style='color: {COLORS['success']};'>Consolidado</span>"
    else:
        return titulo_base

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
    
    # Configurar layout com estilo moderno
    fig.update_layout(
        title=dict(
            text='<b>Comparativo por Setor - Visão Geral</b>',
            x=0,
            font=dict(size=20, color=COLORS['text'], family='Arial Black')
        ),
        xaxis=dict(
            title='<b>Setor</b>',
            titlefont=dict(size=14, color=COLORS['text']),
            tickfont=dict(size=12, color=COLORS['text']),
            tickangle=-45,
            gridcolor='rgba(0,0,0,0.1)',
            showgrid=True
        ),
        yaxis=dict(
            title='<b>Quantidade de Registros</b>',
            titlefont=dict(size=14, color=COLORS['text']),
            tickfont=dict(size=12, color=COLORS['text']),
            gridcolor='rgba(0,0,0,0.1)',
            showgrid=True
        ),
        barmode='group',
        bargap=0.15,
        bargroupgap=0.1,
        legend=dict(
            title='<b>Status</b>',
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            font=dict(size=12, color=COLORS['text'])
        ),
        plot_bgcolor=COLORS['background'],
        paper_bgcolor='white',
        margin=dict(l=60, r=60, t=80, b=60),
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
        backlog_por_status['Backlog_str'] = backlog_por_status['Backlog'].dt.strftime('%B/%Y')
        
        # Criar gráfico de linha moderno
        fig = go.Figure()
        
        # Adicionar linha para Resolvidos
        if 'Resolvido' in backlog_por_status.columns:
            fig.add_trace(go.Scatter(
                x=backlog_por_status['Backlog_str'],
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
                x=backlog_por_status['Backlog_str'],
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
        
        # Configurar layout moderno
        fig.update_layout(
            title=dict(
                text='<b>Evolução Temporal do Backlog</b>',
                x=0,
                font=dict(size=20, color=COLORS['text'], family='Arial Black')
            ),
            xaxis=dict(
                title='<b>Período (Mês/Ano)</b>',
                titlefont=dict(size=14, color=COLORS['text']),
                tickfont=dict(size=12, color=COLORS['text']),
                categoryorder='array', 
                categoryarray=backlog_por_status['Backlog_str'],
                gridcolor='rgba(0,0,0,0.1)',
                showgrid=True
            ),
            yaxis=dict(
                title='<b>Quantidade de Registros</b>',
                titlefont=dict(size=14, color=COLORS['text']),
                tickfont=dict(size=12, color=COLORS['text']),
                gridcolor='rgba(0,0,0,0.1)',
                showgrid=True
            ),
            legend=dict(
                title='<b>Status</b>',
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1,
                font=dict(size=12, color=COLORS['text'])
            ),
            plot_bgcolor=COLORS['background'],
            paper_bgcolor='white',
            margin=dict(l=60, r=60, t=80, b=60),
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
        
        # Agrupar responsáveis com poucos incidentes
        df_status_maior5 = df_status[df_status > 5]
        outros_count = df_status[df_status <= 5].sum()
        
        if outros_count > 0:
            df_status_pizza = pd.concat([
                df_status_maior5, 
                pd.Series([outros_count], index=['Outros'])
            ])
        else:
            df_status_pizza = df_status_maior5
        
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
        
        # Configurar layout moderno
        fig.update_layout(
            title=dict(
                text='<b>Distribuição por Responsáveis</b>',
                x=0,
                font=dict(size=20, color=COLORS['text'], family='Arial Black')
            ),
            annotations=[
                dict(
                    text=f"<b>Total<br>{df_status_pizza.sum()}</b>",
                    x=0.5, y=0.5,
                    font_size=16,
                    font_color=COLORS['text'],
                    showarrow=False
                )
            ],
            legend=dict(
                orientation='v',
                yanchor='middle',
                y=0.5,
                xanchor='left',
                x=1.05,
                font=dict(size=12, color=COLORS['text'])
            ),
            plot_bgcolor=COLORS['background'],
            paper_bgcolor='white',
            margin=dict(l=60, r=120, t=80, b=60),
            height=500
        )
        
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
        df_responsavel_grouped['Percentual_Resolvidos'] = (
            df_responsavel_grouped.get('Resolvido', 0) / df_responsavel_grouped['Total']
        ) * 100
        
        df_responsavel_grouped = df_responsavel_grouped.reset_index()
        
        # Filtrar responsáveis com mais de 5 incidentes
        df_responsavel_maior5 = df_responsavel_grouped[
            df_responsavel_grouped['Total'] > 5
        ].copy()
        
        df_responsavel_menor_igual5 = df_responsavel_grouped[
            df_responsavel_grouped['Total'] <= 5
        ].copy()
        
        # Agrupar "Outros"
        if not df_responsavel_menor_igual5.empty:
            outros = {
                'Responsavel': 'Outros',
                'Resolvido': df_responsavel_menor_igual5.get('Resolvido', 0).sum(),
                'Pendente': df_responsavel_menor_igual5.get('Pendente', 0).sum(),
                'Total': df_responsavel_menor_igual5['Total'].sum(),
            }
            
            if outros['Total'] > 0:
                outros['Percentual_Resolvidos'] = (outros['Resolvido'] / outros['Total']) * 100
            else:
                outros['Percentual_Resolvidos'] = 0
                
            df_responsavel_maior5 = pd.concat([
                df_responsavel_maior5, 
                pd.DataFrame([outros])
            ], ignore_index=True)
        
        df_responsavel_maior5 = df_responsavel_maior5.sort_values(by='Total', ascending=True)
        
        # Adicionar barras com estilo moderno
        traces = [
            ('Pendentes', 'Pendente', COLORS['pending']),
            ('Resolvidos', 'Resolvido', COLORS['resolved'])
        ]
        
        for name, column, color in traces:
            fig.add_trace(go.Bar(
                x=df_responsavel_maior5['Responsavel'],
                y=df_responsavel_maior5.get(column, 0),
                name=name,
                marker=dict(
                    color=color,
                    line=dict(color='white', width=2),
                    pattern_fillmode='overlay'
                ),
                text=df_responsavel_maior5.get(column, 0),
                textposition='inside',
                textfont=dict(size=12, color='white', family='Arial Black'),
                hovertemplate=f'<b>{name}</b><br>' +
                             'Responsável: %{x}<br>' +
                             'Quantidade: %{y}<br>' +
                             '<extra></extra>'
            ))
        
        # Adicionar linha de total como referência
        fig.add_trace(go.Scatter(
            x=df_responsavel_maior5['Responsavel'],
            y=df_responsavel_maior5.get('Total', 0),
            mode='lines+markers',
            name='Total',
            line=dict(color=COLORS['total'], width=3, dash='dash'),
            marker=dict(size=8, color=COLORS['total'], symbol='diamond'),
            hovertemplate='<b>Total</b><br>' +
                         'Responsável: %{x}<br>' +
                         'Total: %{y}<br>' +
                         '<extra></extra>'
        ))
        
        # Adicionar anotações de percentual com estilo melhorado
        for i in range(len(df_responsavel_maior5)):
            fig.add_annotation(
                x=df_responsavel_maior5['Responsavel'].iloc[i],
                y=df_responsavel_maior5.get('Total', 0).iloc[i] + 2,
                text=f"<b>{df_responsavel_maior5['Percentual_Resolvidos'].iloc[i]:.1f}%</b>",
                showarrow=False,
                font=dict(size=12, color=COLORS['text'], family='Arial Black'),
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor=COLORS['text'],
                borderwidth=1
            )
        
        # Configurar layout moderno
        fig.update_layout(
            title=dict(
                text='<b>Desempenho Individual dos Responsáveis</b>',
                x=0,
                font=dict(size=20, color=COLORS['text'], family='Arial Black')
            ),
            xaxis=dict(
                title=dict(
                    text='<b>Responsável</b>',
                    font=dict(size=14, color=COLORS['text'])
                ),
                tickfont=dict(size=12, color=COLORS['text']),
                gridcolor='rgba(128,128,128,0.2)',
                showgrid=True
            ),
            yaxis=dict(
                title=dict(
                    text='<b>Quantidade de Registros</b>',
                    font=dict(size=14, color=COLORS['text'])
                ),
                tickfont=dict(size=12, color=COLORS['text']),
                gridcolor='rgba(128,128,128,0.2)',
                showgrid=True
            ),
            barmode='group',
            bargap=0.15,
            bargroupgap=0.1,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1,
                font=dict(size=12, color=COLORS['text'])
            ),
            plot_bgcolor=COLORS['background'],
            paper_bgcolor='white',
            margin=dict(l=80, r=60, t=100, b=80),
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
    st.markdown(f'<h1 style="text-align: center; color: #2c3e50; margin-bottom: 30px; font-size: 32px; font-weight: 700;">{APP_CONFIG["title"]}</h1>', unsafe_allow_html=True)

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
    # Título principal sem cabeçalho fixo
    st.markdown(
        f'<h1 style="color: #2c3e50; margin-bottom: 10px;">{APP_CONFIG["title"]}</h1>'
        f'<h2 style="color: #6c757d; margin-bottom: 20px; font-size: 18px;">Análise de Dados Consolidados - Backlog</h2>',
        unsafe_allow_html=True
    )
    
    st.sidebar.markdown(
        f"<b>Bem-vindo</b><br>{st.session_state.nome_usuario}", 
        unsafe_allow_html=True
    )

    if st.sidebar.button("Logout"):
        st.session_state.login = False
        st.success("Logout realizado com sucesso!")
        st.rerun()
    
    # Adicionar informações de governança de TI
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <div style='margin-top: 20px; padding: 10px; background-color: #f8f9fa; border-radius: 8px; border-left: 4px solid #2E86AB;'>
            <h4 style='color: #2c3e50; margin: 0 0 8px 0; font-size: 14px;'>📊 Dashboard de Backlog TI</h4>
            <p style='color: #6c757d; margin: 0; font-size: 12px; line-height: 1.4;'>
                Sistema de análise e monitoramento do backlog de tickets dos setores ITI e SPN.
            </p>
            <br>
            <p style='color: #6c757d; margin: 0; font-size: 11px;'>
                <strong>Desenvolvido por:</strong> Governança de TI<br>
                <strong>Finalidade:</strong> Gestão e controle do backlog
            </p>
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
    # Obter setores permitidos para o usuário
    usuario_nome = st.session_state.nome_usuario
    setores_permitidos = obter_setores_permitidos(usuario_nome)
    setores_disponiveis = [
        s for s in df_consolidado['Setor'].unique() 
        if s in setores_permitidos
    ]

    # Filtros do Dashboard
    st.sidebar.header("Filtros")
    setores_selecionados = st.sidebar.multiselect(
        "Setores", 
        setores_disponiveis, 
        default=setores_disponiveis, 
        key="filtro_dashboard_setor"
    )

    # Título dinâmico
    titulo = gerar_titulo_dinamico("Visão Geral do Backlog", setores_selecionados)
    st.markdown(f"<h1>{titulo}</h1>", unsafe_allow_html=True)

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
    
    with col3:
        fig_pizza = criar_grafico_pizza_responsaveis(df_filtrado)
        if fig_pizza:
            st.plotly_chart(fig_pizza, use_container_width=True)
    
    with col4:
        fig_desempenho = criar_grafico_desempenho(df_filtrado)
        st.plotly_chart(fig_desempenho, use_container_width=True)

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
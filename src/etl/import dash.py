import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# ==================== CONFIGURATION ====================
APP_CONFIG = {
    'title': 'Dashboard de Backlog',
    'data_file': os.path.join('data', 'base', 'consolidado.xlsx')
}

# Colors (Matching your Streamlit app)
COLORS = {
    'primary': '#2E86AB',      # Modern Blue
    'secondary': '#A23B72',    # Pink/Purple
    'success': '#F18F01',      # Vibrant Orange
    'pending': '#C73E1D',      # Red
    'resolved': '#2ECC71',     # Vibrant Green
    'total': '#3498DB',        # Light Blue
    'neutral': '#95A5A6',      # Modern Gray
    'background': '#F8F9FA',   # Light Background
    'text': '#2C3E50'          # Dark Text
}

# Users and Sectors Configuration
USUARIOS = {
    "emerson": (os.getenv("USERNAME_EMERSON", "emerson"), "Emerson Cleiton Simette"),
    "willian": (os.getenv("USERNAME_WILLIAN", "willian"), "Willian Jones Rios"),
    "rafael": (os.getenv("USERNAME_RAFAEL", "rafael"), "Rafael Dall'Anese"),
    "admin": (os.getenv("USERNAME_ADMIN", "admin"), "Administrador"),
}

SETORES_POR_USUARIO = {
    "Emerson Cleiton Simette": ["ITI"],
    "Willian Jones Rios": ["SPN"],
    "Rafael Dall'Anese": ["SPN", "ITI"],
    "Administrador": ["SPN", "ITI"],
}

# ==================== DATA LOADING ====================
def load_data():
    """Loads data from Excel file."""
    try:
        return pd.read_excel(APP_CONFIG['data_file'], sheet_name=None)
    except Exception as e:
        print(f"Error loading data: {e}")
        return {}

def process_data(df_dict):
    """Processes and consolidates data from SPN and ITI sheets."""
    try:
        df_spn = df_dict.get('SPN', pd.DataFrame()).copy()
        df_iti = df_dict.get('ITI', pd.DataFrame()).copy()
        
        # Ensure 'Setor' column exists
        if 'Setor' not in df_spn.columns and not df_spn.empty: df_spn['Setor'] = 'SPN'
        if 'Setor' not in df_iti.columns and not df_iti.empty: df_iti['Setor'] = 'ITI'
        
        df = pd.concat([df_spn, df_iti], ignore_index=True)
        
        if 'Data' in df.columns:
            df['Ano'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce').dt.year
            
        if 'Responsavel' in df.columns:
            df['Responsavel'] = df['Responsavel'].str.strip()
            
        return df
    except Exception as e:
        print(f"Error processing data: {e}")
        return pd.DataFrame()

# ==================== APP INITIALIZATION ====================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = APP_CONFIG['title']
server = app.server

# Load Data Initially
raw_data = load_data()
df_consolidado = process_data(raw_data)

# ==================== COMPONENTS ====================

# Sidebar Layout
sidebar = html.Div(
    [
        html.H2("DataPaws", className="display-6", style={'color': COLORS['primary'], 'fontWeight': 'bold'}),
        html.Hr(),
        
        # User Selector (Acts as Login)
        html.Label("👤 Selecione Usuário", className="fw-bold"),
        dcc.Dropdown(
            id="user-selector",
            options=[{'label': name, 'value': key} for key, (_, name) in USUARIOS.items()],
            value=None,
            placeholder="Quem é você?",
            clearable=False,
            className="mb-3"
        ),
        
        # Dynamic Filters Section
        html.Div(id="filter-container", style={"display": "none"}, children=[
            html.Hr(),
            html.H6("FILTROS", className="text-muted small fw-bold"),
            
            html.Label("🏢 Setor", className="mt-2"),
            dcc.Dropdown(id="sector-filter", multi=True, className="mb-2"),
            
            html.Label("📌 Status", className="mt-2"),
            dcc.Dropdown(
                id="status-filter",
                options=[{'label': s, 'value': s} for s in ['Resolvido', 'Pendente']],
                value=['Resolvido', 'Pendente'],
                multi=True,
                className="mb-2"
            ),
        ]),
        
        # Footer Info
        html.Div([
            html.Hr(),
            dbc.Alert([
                html.H6("📊 Dashboard Backlog", className="alert-heading small"),
                html.P("Monitoramento de tickets ITI e SPN.", className="small mb-0")
            ], color="light", className="mt-4")
        ])
    ],
    style={
        "position": "fixed", "top": 0, "left": 0, "bottom": 0, "width": "18rem",
        "padding": "2rem 1rem", "backgroundColor": "#f8f9fa", "borderRight": "1px solid #dee2e6"
    },
)

# Main Content Layout
content = html.Div(id="page-content", style={"marginLeft": "18rem", "padding": "2rem"})

# App Layout
app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

# ==================== CALLBACKS ====================

@app.callback(
    [Output("filter-container", "style"),
     Output("sector-filter", "options"),
     Output("sector-filter", "value"),
     Output("page-content", "children")],
    [Input("user-selector", "value")]
)
def update_user_view(user_key):
    """Updates the view based on the selected user (Authentication simulation)."""
    if not user_key:
        # Welcome / Login Screen
        return {"display": "none"}, [], [], html.Div(
            dbc.Container([
                dbc.Row(
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody([
                                html.H1("Bem-vindo ao DataPaws", className="text-center text-primary mb-4"),
                                html.P("Por favor, selecione seu usuário no menu lateral para acessar o dashboard.", className="text-center lead"),
                                html.Div(className="d-flex justify-content-center", children=[
                                    html.I(className="bi bi-arrow-left-circle", style={"fontSize": "2rem"})
                                ])
                            ]),
                            className="shadow-sm border-0", style={"marginTop": "100px"}
                        ),
                        width={"size": 8, "offset": 2}
                    )
                )
            ]),
        )
    
    # User Authenticated
    full_name = USUARIOS[user_key][1]
    allowed_sectors = SETORES_POR_USUARIO.get(full_name, [])
    sector_options = [{'label': s, 'value': s} for s in allowed_sectors]
    
    # Dashboard Layout
    dashboard_layout = html.Div([
        html.Div([
            html.H2(f"Visão Geral - {', '.join(allowed_sectors)}", className="fw-bold"),
            html.P(f"Bem-vindo, {full_name}", className="text-muted")
        ], className="mb-4"),
        
        # KPI Row
        dbc.Row(id="kpi-row", className="mb-4"),
        
        # Charts Row 1
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Comparativo por Setor"),
                dbc.CardBody(dcc.Graph(id="chart-comparativo", config={'displayModeBar': False}))
            ], className="shadow-sm border-0 h-100"), md=6, className="mb-4"),
            
            dbc.Col(dbc.Card([
                dbc.CardHeader("Evolução do Backlog"),
                dbc.CardBody(dcc.Graph(id="chart-backlog", config={'displayModeBar': False}))
            ], className="shadow-sm border-0 h-100"), md=6, className="mb-4"),
        ]),
        
        # Charts Row 2 (Performance)
        html.H4("Desempenho por Responsável (Pendentes)", className="mb-3 text-muted"),
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Equipe ITI"),
                dbc.CardBody(dcc.Graph(id="chart-performance-iti", config={'displayModeBar': False}))
            ], className="shadow-sm border-0"), md=6, className="mb-4"),
            
            dbc.Col(dbc.Card([
                dbc.CardHeader("Equipe SPN"),
                dbc.CardBody(dcc.Graph(id="chart-performance-spn", config={'displayModeBar': False}))
            ], className="shadow-sm border-0"), md=6, className="mb-4"),
        ])
    ])
    
    return {"display": "block"}, sector_options, allowed_sectors, dashboard_layout

@app.callback(
    [Output("kpi-row", "children"),
     Output("chart-comparativo", "figure"),
     Output("chart-backlog", "figure"),
     Output("chart-performance-iti", "figure"),
     Output("chart-performance-spn", "figure")],
    [Input("sector-filter", "value"),
     Input("status-filter", "value")]
)
def update_dashboard(selected_sectors, selected_status):
    """Updates all charts and KPIs based on filters."""
    if not selected_sectors:
        return [], go.Figure(), go.Figure(), go.Figure(), go.Figure()
    
    # Filter Data
    mask = df_consolidado['Setor'].isin(selected_sectors) & df_consolidado['Status'].isin(selected_status)
    df_filtered = df_consolidado[mask]
    
    # 1. KPIs
    total = len(df_filtered)
    resolved = len(df_filtered[df_filtered['Status'] == 'Resolvido'])
    pending = len(df_filtered[df_filtered['Status'] == 'Pendente'])
    
    kpi_cards = [
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("TOTAL REGISTROS", className="card-subtitle text-muted mb-2"),
                html.H2(f"{total}", className="card-title text-primary")
            ])
        ], className="shadow-sm border-0 border-start border-5 border-primary"), md=4),
        
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("RESOLVIDOS", className="card-subtitle text-muted mb-2"),
                html.H2(f"{resolved}", className="card-title text-success")
            ])
        ], className="shadow-sm border-0 border-start border-5 border-success"), md=4),
        
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("PENDENTES", className="card-subtitle text-muted mb-2"),
                html.H2(f"{pending}", className="card-title text-danger")
            ])
        ], className="shadow-sm border-0 border-start border-5 border-danger"), md=4),
    ]
    
    # 2. Chart: Comparativo Setor (Stacked Bar)
    # Prepare data: Group by Sector and Status
    df_grouped = df_filtered.groupby(['Setor', 'Status']).size().unstack(fill_value=0)
    
    fig_comp = go.Figure()
    if 'Pendente' in df_grouped.columns:
        fig_comp.add_trace(go.Bar(x=df_grouped.index, y=df_grouped['Pendente'], name='Pendentes', marker_color=COLORS['pending']))
    if 'Resolvido' in df_grouped.columns:
        fig_comp.add_trace(go.Bar(x=df_grouped.index, y=df_grouped['Resolvido'], name='Resolvidos', marker_color=COLORS['resolved']))
    
    fig_comp.update_layout(barmode='stack', margin=dict(l=20, r=20, t=20, b=20), height=350, legend=dict(orientation="h", y=1.1))
    
    # 3. Chart: Backlog Evolution
    if 'Backlog' in df_filtered.columns:
        df_time = df_filtered.copy()
        df_time['Backlog'] = pd.to_datetime(df_time['Backlog'], format='%m/%Y', errors='coerce')
        time_counts = df_time.groupby(['Backlog', 'Status']).size().unstack(fill_value=0).reset_index()
        time_counts = time_counts.sort_values('Backlog')
        
        fig_backlog = go.Figure()
        if 'Resolvido' in time_counts.columns:
            fig_backlog.add_trace(go.Scatter(x=time_counts['Backlog'], y=time_counts['Resolvido'], name='Resolvidos', 
                                            line=dict(color=COLORS['resolved'], width=3), mode='lines+markers'))
        if 'Pendente' in time_counts.columns:
            fig_backlog.add_trace(go.Scatter(x=time_counts['Backlog'], y=time_counts['Pendente'], name='Pendentes', 
                                            line=dict(color=COLORS['pending'], width=3), mode='lines+markers'))
        fig_backlog.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=350, legend=dict(orientation="h", y=1.1))
    else:
        fig_backlog = go.Figure().update_layout(title="Dados temporais indisponíveis")

    # 4 & 5. Performance Charts (Horizontal Bars)
    def create_perf_chart(sector_name):
        # Filter for Sector AND Status='Pendente' (as per original logic for performance)
        df_sec = df_filtered[(df_filtered['Setor'] == sector_name) & (df_filtered['Status'] == 'Pendente')]
        
        if df_sec.empty: 
            return go.Figure().update_layout(
                xaxis={'visible': False}, yaxis={'visible': False}, 
                annotations=[dict(text="Sem pendências", xref="paper", yref="paper", showarrow=False, font=dict(size=14))]
            )
            
        resp_counts = df_sec['Responsavel'].value_counts().head(8).sort_values(ascending=True) # Sort for correct bar order
        
        fig = go.Figure(go.Bar(
            y=resp_counts.index, 
            x=resp_counts.values, 
            orientation='h',
            marker_color=COLORS['pending'],
            text=resp_counts.values,
            textposition='auto'
        ))
        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)
        return fig

    return kpi_cards, fig_comp, fig_backlog, create_perf_chart("ITI"), create_perf_chart("SPN")

if __name__ == "__main__":
    app.run(debug=True)
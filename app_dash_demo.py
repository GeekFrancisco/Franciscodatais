import dash
from dash import html, dcc, Input, Output, State
import plotly.express as px
import pandas as pd
import os

# ==================== USUÁRIOS (Login/Senha) ====================
# EM PRODUÇÃO: NUNCA coloque senhas hardcoded assim. Use variáveis de ambiente ou Banco de Dados.
# Isso é apenas para demonstração.
VALID_USERNAME_PASSWORD_PAIRS = {
    'admin': '1234',
    'gestor': 'senha_gestor'
}

# Inicializar o App Dash
# Comparado ao Streamlit, aqui você cria uma "instância" do app
# suppress_callback_exceptions=True é necessário para layouts dinâmicos
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# ==================== DADOS (Simulação) ====================
# Tentar ler o arquivo real, se não der, usar dados fictícios
file_path = 'data/base/consolidado.xlsx'
try:
    df = pd.read_excel(file_path)
    # Limpeza básica (adaptado do seu código original)
    if 'Responsavel' in df.columns:
        df = df.dropna(subset=['Responsavel'])
except Exception as e:
    print(f"Erro ao ler arquivo: {e}. Usando dados de exemplo.")
    data = {
        'Responsavel': ['Emerson', 'Willian', 'Rafael', 'Emerson', 'Willian'],
        'Status': ['Pendente', 'Concluído', 'Pendente', 'Pendente', 'Concluído'],
        'Prioridade': ['Alta', 'Média', 'Baixa', 'Alta', 'Média']
    }
    df = pd.DataFrame(data)

# ==================== LAYOUTS ====================

# Layout de Login
login_layout = html.Div(
    style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'height': '100vh', 'backgroundColor': '#f0f2f6'},
    children=[
        html.Div(
            style={'backgroundColor': 'white', 'padding': '40px', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'},
            children=[
                html.H2("Login", style={'textAlign': 'center', 'color': '#2E86AB', 'marginBottom': '20px'}),
                dcc.Input(id='username-box', type='text', placeholder='Usuário', style={'width': '100%', 'padding': '10px', 'marginBottom': '10px', 'boxSizing': 'border-box'}),
                dcc.Input(id='password-box', type='password', placeholder='Senha', style={'width': '100%', 'padding': '10px', 'marginBottom': '20px', 'boxSizing': 'border-box'}),
                html.Button('Entrar', id='login-button', n_clicks=0, style={'width': '100%', 'padding': '10px', 'backgroundColor': '#2E86AB', 'color': 'white', 'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer'}),
                html.Div(id='login-output', style={'color': 'red', 'marginTop': '10px', 'textAlign': 'center'})
            ]
        )
    ]
)

# Layout Principal (Dashboard)
dashboard_layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '20px'}, children=[
    
    html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}, children=[
        html.H1("Dashboard Backlog (Versão Dash)", style={'color': '#2E86AB'}),
        html.Button('Sair', id='logout-button', n_clicks=0, style={'padding': '5px 15px', 'backgroundColor': '#ff4b4b', 'color': 'white', 'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer'})
    ]),
    
    html.Div([
        html.P("Esta é uma demonstração de como o Dash funciona. Note que o layout é definido via componentes HTML."),
        html.P("Selecione um Responsável abaixo para filtrar o gráfico:")
    ], style={'marginBottom': '20px'}),

    # Dropdown (Filtro)
    dcc.Dropdown(
        id='filtro-responsavel',
        options=[{'label': i, 'value': i} for i in df['Responsavel'].unique()],
        value=None, # Valor inicial
        placeholder="Selecione um responsável...",
        style={'width': '50%'}
    ),

    # Gráfico
    dcc.Graph(id='grafico-barras'),
    
    html.Div(id='output-texto', style={'marginTop': '20px', 'fontWeight': 'bold'})
])

# Layout Raiz (Controla qual tela mostrar)
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='login-state', data={'logged_in': False}),
    html.Div(id='page-content')
])

# ==================== CALLBACKS (Lógica) ====================

# Callback de Login/Logout e Navegação
@app.callback(
    [Output('login-state', 'data'),
     Output('page-content', 'children')],
    [Input('login-button', 'n_clicks'),
     Input('logout-button', 'n_clicks')],
    [State('username-box', 'value'),
     State('password-box', 'value'),
     State('login-state', 'data')]
)
def manage_login(login_clicks, logout_clicks, username, password, current_state):
    ctx = dash.callback_context
    if not ctx.triggered:
        return current_state, login_layout if not current_state['logged_in'] else dashboard_layout
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'login-button':
        if username in VALID_USERNAME_PASSWORD_PAIRS and VALID_USERNAME_PASSWORD_PAIRS[username] == password:
            return {'logged_in': True}, dashboard_layout
        elif username or password:
            # Retorna layout de login com erro (idealmente faria update só da mensagem, mas simplificando aqui)
            # Para simplificar, vamos retornar o layout de login de novo, mas o erro seria tratado em outro callback se quiséssemos ser mais precisos.
            # Aqui vamos usar um truque: se falhar, retorna login. O usuário vai ver que não entrou.
            return {'logged_in': False}, login_layout
            
    if button_id == 'logout-button':
        return {'logged_in': False}, login_layout
        
    return current_state, login_layout if not current_state['logged_in'] else dashboard_layout

# Callback para exibir erro de login (separado para não resetar o layout inteiro)
@app.callback(
    Output('login-output', 'children'),
    [Input('login-button', 'n_clicks')],
    [State('username-box', 'value'),
     State('password-box', 'value')]
)
def show_login_error(n_clicks, username, password):
    if n_clicks > 0:
        if username not in VALID_USERNAME_PASSWORD_PAIRS or VALID_USERNAME_PASSWORD_PAIRS[username] != password:
            return "Usuário ou senha incorretos."
    return ""


# Callback do Dashboard (só roda se estiver logado e os componentes existirem)
@app.callback(
    [Output('grafico-barras', 'figure'),
     Output('output-texto', 'children')],
    [Input('filtro-responsavel', 'value')]
)
def atualizar_grafico(responsavel_selecionado):
    dff = df.copy()
    
    texto = "Mostrando todos os dados."
    
    if responsavel_selecionado:
        dff = dff[dff['Responsavel'] == responsavel_selecionado]
        texto = f"Filtrado por: {responsavel_selecionado}"
    
    # Criar gráfico com Plotly Express
    # Contagem por Status
    if 'Status' in dff.columns:
        contagem = dff['Status'].value_counts().reset_index()
        contagem.columns = ['Status', 'Quantidade']
        fig = px.bar(contagem, x='Status', y='Quantidade', title="Tarefas por Status", color='Status')
    else:
        # Fallback se não tiver coluna Status
        fig = px.bar(x=[1,2], y=[1,2], title="Dados insuficientes para gráfico")

    return fig, texto

# ==================== EXECUÇÃO ====================
if __name__ == '__main__':
    # debug=True faz o hot-reload (igual ao Streamlit)
    app.run(debug=True, port=8052)

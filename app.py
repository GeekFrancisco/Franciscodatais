import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import hashlib
import secrets
import datetime
from functools import wraps

# Configurações iniciais
load_dotenv()

# Constantes
PAGE_TITLE = "DataPaws"
PAGE_ICON = "Base/IMG/Designer.jpeg"
DATA_PATH = 'Base/consolidado.xlsx'
CHART_COLORS = {
    'total': 'skyblue',
    'resolved': 'lightgreen',
    'pending': 'salmon',
    'status_lines': ['blue', 'red', 'green']
}
MIN_PERCENTAGE_FOR_PIE = 5

@dataclass
class Usuario:
    username: str
    senha_hash: str
    salt: str
    nome_completo: str
    ultimo_acesso: datetime.datetime = None

class SecurityManager:
    def __init__(self):
        self._initialize_security()
    
    def _initialize_security(self):
        """Inicializa configurações de segurança"""
        self.max_attempts = 3
        self.lockout_duration = 300  # 5 minutos
        self.failed_attempts = {}
        self.locked_accounts = {}
    
    def is_account_locked(self, username: str) -> bool:
        """Verifica se uma conta está bloqueada"""
        if username in self.locked_accounts:
            lock_time = self.locked_accounts[username]
            if (datetime.datetime.now() - lock_time).seconds < self.lockout_duration:
                return True
            del self.locked_accounts[username]
        return False
    
    def record_failed_attempt(self, username: str):
        """Registra uma tentativa falha de login"""
        current_time = datetime.datetime.now()
        if username not in self.failed_attempts:
            self.failed_attempts[username] = []
        
        self.failed_attempts[username].append(current_time)
        
        # Remove tentativas antigas (mais de 1 hora)
        self.failed_attempts[username] = [
            attempt for attempt in self.failed_attempts[username]
            if (current_time - attempt).seconds < 3600
        ]
        
        if len(self.failed_attempts[username]) >= self.max_attempts:
            self.locked_accounts[username] = current_time
    
    def clear_failed_attempts(self, username: str):
        """Limpa as tentativas falhas após login bem-sucedido"""
        if username in self.failed_attempts:
            del self.failed_attempts[username]

class AuthManager:
    def __init__(self):
        self.usuarios = self._inicializar_usuarios()
        self.security = SecurityManager()
    
    def _hash_senha(self, senha: str, salt: str = None) -> Tuple[str, str]:
        if salt is None:
            salt = secrets.token_hex(16)
        senha_completa = senha + salt
        return hashlib.sha256(senha_completa.encode()).hexdigest(), salt
    
    def _inicializar_usuarios(self) -> Dict[str, Usuario]:
        usuarios = {}
        usernames = ['emerson', 'willian', 'rafael', 'admin']
        
        for username in usernames:
            senha_env = os.getenv(f"PASSWORD_{username.upper()}")
            if senha_env:
                salt = secrets.token_hex(16)
                senha_hash, _ = self._hash_senha(senha_env, salt)
                
                usuarios[username] = Usuario(
                    username=username,
                    senha_hash=senha_hash,
                    salt=salt,
                    nome_completo=os.getenv(f"FULLNAME_{username.upper()}", f"User {username}")
                )
        
        return usuarios

    def verificar_login(self, username: str, senha_tentativa: str) -> Optional[str]:
        username = username.lower()
        
        if self.security.is_account_locked(username):
            return None
            
        usuario = self.usuarios.get(username)
        if not usuario:
            self.security.record_failed_attempt(username)
            return None
            
        senha_hash_tentativa, _ = self._hash_senha(senha_tentativa, usuario.salt)
        
        if secrets.compare_digest(senha_hash_tentativa, usuario.senha_hash):
            self.security.clear_failed_attempts(username)
            usuario.ultimo_acesso = datetime.datetime.now()
            return usuario.nome_completo
            
        self.security.record_failed_attempt(username)
        return None

class DataManager:
    @staticmethod
    @st.cache_data
    def carregar_dados(caminho_arquivo: str) -> Dict[str, pd.DataFrame]:
        """Carrega e faz cache dos dados do Excel"""
        return pd.read_excel(caminho_arquivo, sheet_name=None)
    
    @staticmethod
    def processar_dados(df_dados: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Processa e combina os dados das diferentes abas"""
        df_spn = df_dados['SPN'].copy()
        df_iti = df_dados['ITI'].copy()
        
        # Adiciona identificador da origem
        df_spn['Aba'] = 'SPN'
        df_iti['Aba'] = 'ITI'
        
        return pd.concat([df_spn, df_iti], ignore_index=True)
    
    @staticmethod
    def calcular_estatisticas(df: pd.DataFrame) -> Dict[str, float]:
        """Calcula estatísticas gerais dos dados"""
        total_registros = len(df)
        total_resolvidos = len(df[df['Status'] == 'Resolvido'])
        total_pendentes = total_registros - total_resolvidos
        
        return {
            'total': total_registros,
            'resolvidos': total_resolvidos,
            'pendentes': total_pendentes,
            'perc_resolvidos': (total_resolvidos / total_registros * 100) if total_registros > 0 else 0,
            'perc_pendentes': (total_pendentes / total_registros * 100) if total_registros > 0 else 0
        }

class ChartManager:
    @staticmethod
    def criar_grafico_incidentes(df: pd.DataFrame) -> go.Figure:
        """Cria gráfico de barras comparativo de incidentes"""
        df_total = df['Setor'].value_counts()
        df_resolved = df[df['Status'] == 'Resolvido']['Setor'].value_counts()
        df_pending = df_total - df_resolved.reindex(df_total.index, fill_value=0)
        
        fig = go.Figure()
        
        for data, name, color in [
            (df_total, 'Total', CHART_COLORS['total']),
            (df_resolved.reindex(df_total.index, fill_value=0), 'Resolvidos', CHART_COLORS['resolved']),
            (df_pending, 'Pendentes', CHART_COLORS['pending'])
        ]:
            fig.add_trace(go.Bar(
                x=df_total.index,
                y=data.values,
                name=name,
                marker_color=color,
                text=[f'{val} ({(val/df_total.sum()*100):.1f}%)' for val in data.values],
                textposition='inside'
            ))
        
        fig.update_layout(
            title='Comparativo entre Total, Resolvidos e Pendentes',
            xaxis_title='Setor',
            yaxis_title='Quantidade',
            barmode='group',
            legend_title='Tipo de Incidente',
            xaxis_tickangle=-45
        )
        
        return fig
    
    @staticmethod
    def criar_grafico_backlog(df: pd.DataFrame) -> Optional[go.Figure]:
        """Cria gráfico de linha para análise de backlog"""
        if 'Backlog' not in df.columns:
            return None
            
        backlog_por_status = (
            df.groupby(['Backlog', 'Status'])
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )
        
        backlog_por_status['Total'] = backlog_por_status.sum(axis=1, numeric_only=True)
        
        fig = px.line(
            backlog_por_status,
            x='Backlog',
            y=['Resolvido', 'Pendente', 'Total'],
            labels={'Backlog': 'Mês/Ano', 'value': 'Contagem', 'variable': 'Status'},
            title="Distribuição de Incidentes por Status",
            markers=True,
            color_discrete_sequence=CHART_COLORS['status_lines']
        )
        
        for trace in fig.data:
            for x, y in zip(backlog_por_status['Backlog'], trace.y):
                fig.add_annotation(
                    x=x,
                    y=y,
                    text=str(y),
                    showarrow=True,
                    arrowhead=2,
                    ax=0,
                    ay=-10,
                    font=dict(size=10)
                )
        
        return fig
    
    @staticmethod
    def criar_grafico_responsaveis(df: pd.DataFrame) -> Optional[go.Figure]:
        """Cria gráfico de pizza para distribuição por responsáveis"""
        if 'Responsavel' not in df.columns:
            return None
            
        df_status = df.drop_duplicates(subset=['Responsavel', 'Incidente']).groupby('Responsavel').size()
        total = df_status.sum()
        percentages = df_status / total * 100
        
        df_status_grouped = df_status[percentages >= MIN_PERCENTAGE_FOR_PIE]
        other_count = df_status[percentages < MIN_PERCENTAGE_FOR_PIE].sum()
        
        if other_count > 0:
            df_status_grouped['Outros'] = other_count
            
        if not df_status_grouped.empty:
            fig = px.pie(
                df_status_grouped,
                names=df_status_grouped.index,
                values=df_status_grouped.values,
                title='Distribuição Backlog por Responsáveis',
                hole=0.3
            )
            fig.update_traces(textinfo='percent')
            return fig
        return None
    
    @staticmethod
    def criar_grafico_desempenho(df: pd.DataFrame) -> Optional[go.Figure]:
        """Cria gráfico de barras para análise de desempenho"""
        if 'Responsavel' not in df.columns:
            return None
            
        df_responsavel = (
            df.drop_duplicates(subset=['Responsavel', 'Incidente'])
            .groupby(['Responsavel', 'Status'])
            .size()
            .unstack(fill_value=0)
        )
        
        df_responsavel['Total'] = df_responsavel.sum(axis=1)
        df_responsavel['Percentual Resolvidos'] = (
            df_responsavel.get('Resolvido', 0) / df_responsavel['Total']
        ) * 100
        
        df_responsavel = df_responsavel.sort_values(
            by='Total', ascending=False
        ).reset_index()
        
        fig = go.Figure()
        
        for data, name, color in [
            (df_responsavel['Total'], 'Total', 'lightblue'),
            (df_responsavel['Resolvido'], 'Resolvidos', 'lightgreen')
        ]:
            fig.add_trace(go.Bar(
                x=df_responsavel['Responsavel'],
                y=data,
                name=name,
                marker_color=color,
                text=data,
                textposition='inside'
            ))
            
        for i in range(len(df_responsavel)):
            fig.add_annotation(
                x=df_responsavel['Responsavel'][i],
                y=df_responsavel['Resolvido'][i],
                text=f"{df_responsavel['Percentual Resolvidos'][i]:.1f}%",
                showarrow=True,
                arrowhead=2,
                ax=0,
                ay=-30,
                font=dict(size=10)
            )
            
        fig.update_layout(
            title='Desempenho dos Responsáveis',
            xaxis_title='Responsável',
            yaxis_title='Quantidade',
            barmode='group',
            legend_title='Tipo'
        )
        
        return fig

class UIManager:
    @staticmethod
    def aplicar_estilos():
        """Aplica estilos CSS personalizados"""
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
            .stButton button {
                width: 100%;
            }
            </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def mostrar_cabecalho():
        """Mostra o cabeçalho fixo da aplicação"""
        st.markdown(
            '<div class="fixed-header">'
            '<h1>DataPaws</h1>'
            '<h2>Análise de Dados Consolidados - Backlog</h2>'
            '</div>',
            unsafe_allow_html=True
        )
    
    @staticmethod
    def mostrar_sidebar(nome_usuario: str, df: pd.DataFrame) -> List[str]:
        """Configura e mostra a barra lateral"""
        st.sidebar.header(f"{nome_usuario}")
        
        if st.sidebar.button("Logout"):
            st.session_state.login = False
            st.rerun()
        
        st.sidebar.header("Filtros por Área")
        setores_disponiveis = df['Setor'].unique()
        return [setor for setor in setores_disponiveis if st.sidebar.checkbox(setor, value=True)]
    
    @staticmethod
    def mostrar_estatisticas(stats: Dict[str, float]):
        """Mostra as estatísticas gerais"""
        st.write(
            f"**Total de Registros:** {stats['total']} "
            f"**Resolvidos:** {stats['resolvidos']} ({stats['perc_resolvidos']:.1f}%) "
            f"**Pendentes:** {stats['pendentes']} ({stats['
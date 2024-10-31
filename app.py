import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Configuração inicial da página do Streamlit
st.set_page_config(page_title="Dados Consolidados", layout="wide")

# Caminho para o arquivo Excel consolidado
caminho_arquivo = 'Base/consolidado.xlsx'  # Usando caminho relativo

# Função para carregar as abas de dados do arquivo Excel consolidado
@st.cache_data
def carregar_dados(caminho_arquivo):
    """Carrega as abas SPN e ITI de um arquivo Excel consolidado e as retorna como DataFrames."""
    try:
        df_spn = pd.read_excel(caminho_arquivo, sheet_name='SPN')
        df_iti = pd.read_excel(caminho_arquivo, sheet_name='ITI')
        return df_spn, df_iti
    except FileNotFoundError:
        st.error("Arquivo não encontrado. Verifique o caminho e tente novamente.")
        return pd.DataFrame(), pd.DataFrame()  # Retorna DataFrames vazios
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar os dados: {e}")
        return pd.DataFrame(), pd.DataFrame()  # Retorna DataFrames vazios

# Verifica se o arquivo existe
if not pd.io.common.file_exists(caminho_arquivo):
    st.error(f"O arquivo {caminho_arquivo} não foi encontrado.")
else:
    # Carrega as abas SPN e ITI
    df_spn, df_iti = carregar_dados(caminho_arquivo)

    # Combina os dados e adiciona uma coluna para identificar a aba de origem
    df_spn['Aba'] = 'SPN'
    df_iti['Aba'] = 'ITI'
    df_consolidado = pd.concat([df_spn, df_iti], ignore_index=True)

    # Barra lateral para filtros
    st.sidebar.header("Filtros")

    # Filtro de Aba
    aba_selecionada = st.sidebar.selectbox("Selecionar Área", options=['Todas', 'SPN', 'ITI'])

    # Filtro de Semana
    semanas_unicas = df_consolidado['Semana'].dropna().unique()
    semana_selecionada = st.sidebar.selectbox("Selecionar Semana", options=['Todas'] + sorted(semanas_unicas))

    # Aplicar filtros ao DataFrame consolidado
    df_filtrado = df_consolidado.copy()
    if aba_selecionada != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['Aba'] == aba_selecionada]

    if semana_selecionada != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['Semana'] == semana_selecionada]

    # Exibir título da página principal
    st.title("Análise de Dados Consolidados")

    # Exibir total de registros após aplicação dos filtros
    st.write(f"**Total de Registros:** {len(df_filtrado)}")
    st.dataframe(df_filtrado.drop(columns=['Aba']))  # Oculta a coluna "Aba"

    # Gráfico 1: Quantidade de incidentes por setor
    st.header("Quantidade de Incidentes por Setor")

    if not df_filtrado.empty:
        df_total_sector = df_filtrado['Setor'].value_counts()
        df_resolved = df_filtrado[df_filtrado['Status'] == 'Resolvido']
        df_resolved_sector = df_resolved['Setor'].value_counts()

        df_unresolved_sector = df_total_sector - df_resolved_sector.reindex(df_total_sector.index, fill_value=0)

        # Criar o gráfico
        fig_incidentes = go.Figure()
        fig_incidentes.add_trace(go.Bar(
            x=df_total_sector.index,
            y=df_total_sector.values,
            name='Total',
            marker_color='skyblue',
            text=[f'{val} ({(val / df_total_sector.sum() * 100):.1f}%)' for val in df_total_sector.values],
            textposition='inside'
        ))

        fig_incidentes.add_trace(go.Bar(
            x=df_resolved_sector.index,
            y=df_resolved_sector.reindex(df_total_sector.index, fill_value=0).values,
            name='Resolvidos',
            marker_color='lightgreen',
            text=[f'{val} ({(val / df_total_sector.sum() * 100):.1f}%)' for val in df_resolved_sector.reindex(df_total_sector.index, fill_value=0).values],
            textposition='inside'
        ))

        fig_incidentes.add_trace(go.Bar(
            x=df_unresolved_sector.index,
            y=df_unresolved_sector.values,
            name='Pendentes',
            marker_color='salmon',
            text=[f'{val} ({(val / df_total_sector.sum() * 100):.1f}%)' for val in df_unresolved_sector.values],
            textposition='inside'
        ))

        fig_incidentes.update_layout(
            title='Comparativo entre Total, Resolvidos e Pendentes',
            xaxis_title='Setor',
            yaxis_title='Quantidade',
            barmode='group',
            legend_title='Tipo de Incidente',
            xaxis_tickangle=-45
        )

        st.plotly_chart(fig_incidentes, use_container_width=True)

    # Gráfico de Linha para Status concluído, não concluído e total
    st.subheader("Distribuição de Incidentes por Mês/Ano e Status")

    if 'Backlog' in df_filtrado.columns:
        df_filtrado['Backlog'] = pd.to_datetime(df_filtrado['Backlog'], errors='coerce')

        backlog_por_status = (
            df_filtrado.groupby(['Backlog', 'Status'])
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )

        backlog_por_status['Total'] = backlog_por_status.sum(axis=1, numeric_only=True)

        status_columns = ['Resolvido', 'Pendente', 'Total']
        for col in status_columns:
            if col not in backlog_por_status.columns:
                backlog_por_status[col] = 0

        colors = ['blue', 'red', 'green']

        fig_backlog_status = px.line(
            backlog_por_status,
            x='Backlog',
            y=['Resolvido', 'Pendente', 'Total'],
            labels={'Backlog': 'Mês/Ano', 'value': 'Contagem', 'variable': 'Status'},
            title="Distribuição de Incidentes por Status",
            markers=True,
            color_discrete_sequence=colors
        )

        for col in ['Resolvido', 'Pendente', 'Total']:
            fig_backlog_status.add_trace(
                go.Scatter(
                    x=backlog_por_status['Backlog'],
                    y=backlog_por_status[col],
                    mode='markers+text',
                    name=col,
                    text=backlog_por_status[col].astype(str),
                    textposition='top center',
                    marker=dict(size=8),
                    showlegend=False
                )
            )

        fig_backlog_status.update_layout(
            xaxis_title="Mês/Ano",
            yaxis_title="Contagem",
            showlegend=True
        )

        st.plotly_chart(fig_backlog_status, use_container_width=True)

    # Gráfico de Pizza: Distribuição Backlog Responsáveis
    st.subheader("Distribuição Backlog Responsáveis")

    if 'Responsavel' in df_filtrado.columns:
        df_status = df_filtrado['Responsavel'].value_counts()
        total = df_status.sum()
        percentages = df_status / total * 100

        df_status_grouped = df_status[percentages >= 5]
        other_count = df_status[percentages < 5].sum()

        if other_count > 0:
            df_status_grouped['Outros'] = other_count

        if not df_status_grouped.empty:
            fig_responsaveis = px.pie(
                df_status_grouped,
                names=df_status_grouped.index,
                values=df_status_grouped.values,
                title='Distribuição Backlog por Responsáveis',
                hole=0.3
            )
            st.plotly_chart(fig_responsaveis, use_container_width=True)

    # Gráfico 4: Desempenho dos Responsáveis
    st.subheader("Desempenho dos Responsáveis")

    if 'Responsavel' in df_filtrado.columns:
        df_responsavel = df_filtrado['Responsavel'].value_counts()
        resolved_by_responsavel = df_filtrado[df_filtrado['Status'] == 'Resolvido']['Responsavel'].value_counts()

        percent_resolved = (resolved_by_responsavel / df_responsavel) * 100

        df_desempenho = pd.DataFrame({
            'Total': df_responsavel,
            'Resolvidos': resolved_by_responsavel,
            'Percentual Resolvidos': percent_resolved.fillna(0)
        }).reset_index()

        df_desempenho.columns = ['Responsável', 'Total', 'Resolvidos', 'Percentual Resolvidos']

        fig_desempenho = go.Figure()
        fig_desempenho.add_trace(go.Bar(
            x=df_desempenho['Responsável'],
            y=df_desempenho['Total'],
            name='Total',
            marker_color='lightblue',
            text=df_desempenho['Total'],
            textposition='auto'
        ))

        fig_desempenho.add_trace(go.Bar(
            x=df_desempenho['Responsável'],
            y=df_desempenho['Resolvidos'],
            name='Resolvidos',
            marker_color='lightgreen',
            text=df_desempenho['Resolvidos'],
            textposition='auto'
        ))

        fig_desempenho.update_layout(
            title='Desempenho dos Responsáveis',
            xaxis_title='Responsável',
            yaxis_title='Quantidade',
            barmode='group',
            legend_title='Tipo'
        )

        for i in range(len(df_desempenho)):
            fig_desempenho.add_annotation(
                x=df_desempenho['Responsável'][i],
                y=df_desempenho['Resolvidos'][i],
                text=f"{df_desempenho['Percentual Resolvidos'][i]:.1f}%",
                showarrow=True,
                arrowhead=2,
                ax=0,
                ay=-30,
                font=dict(size=10)
            )

        st.plotly_chart(fig_desempenho, use_container_width=True)

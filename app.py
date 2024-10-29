import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go  # Importar go para gráficos personalizados

# Configuração inicial da página do Streamlit
st.set_page_config(page_title="Dados Consolidados", layout="wide")

# Função para carregar as abas de dados do arquivo Excel consolidado
@st.cache_data
def carregar_dados(caminho_arquivo):
    """Carrega as abas SPN e ITI de um arquivo Excel consolidado e as retorna como DataFrames."""
    df_spn = pd.read_excel(caminho_arquivo, sheet_name='SPN')
    df_iti = pd.read_excel(caminho_arquivo, sheet_name='ITI')
    return df_spn, df_iti

# Caminho para o arquivo Excel consolidado
caminho_arquivo = 'Base/consolidado.xlsx'  # Usando caminho relativo

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

# Exibir total de registros após aplicação dos filtros, sem a coluna "Aba"
st.write(f"**Total de Registros:** {len(df_filtrado)}")
st.dataframe(df_filtrado.drop(columns=['Aba']))  # Oculta a coluna "Aba"

# Gráfico 1: Quantidade de incidentes por setor (total, resolvidos e pendentes)
st.header("Quantidade de Incidentes por Setor")

if not df_filtrado.empty:
    # Total de incidentes por setor
    df_total_sector = df_filtrado['Setor'].value_counts()
    df_resolved = df_filtrado[df_filtrado['Status'] == 'Resolvido']  # Filtrar apenas os resolvidos
    df_resolved_sector = df_resolved['Setor'].value_counts()  # Total de incidentes resolvidos por setor

    # Calcular o total de incidentes não resolvidos
    df_unresolved_sector = df_total_sector - df_resolved_sector.reindex(df_total_sector.index, fill_value=0)

    # Criar um gráfico de barras com três conjuntos de dados
    bar_width = 0.25  # Largura das barras
    indices = np.arange(len(df_total_sector.index))  # Índices para as barras

    # Criar a figura do gráfico
    fig_incidentes = go.Figure()

    # Adicionar as barras ao gráfico
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

# Preparar os dados para o gráfico de linha por mês/ano e status
if 'Backlog' in df_filtrado.columns:
    # Converter coluna 'Backlog' para o tipo datetime, se possível
    df_filtrado['Backlog'] = pd.to_datetime(df_filtrado['Backlog'], errors='coerce')
    
    # Filtra e agrega por Backlog e Status
    backlog_por_status = (
        df_filtrado.groupby(['Backlog', 'Status'])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    # Adicionar coluna "Total" para somar todos os status
    backlog_por_status['Total'] = backlog_por_status.sum(axis=1, numeric_only=True)

    # Verifica se as colunas esperadas estão presentes no DataFrame
    status_columns = ['Resolvido', 'Pendente', 'Total']
    for col in status_columns:
        if col not in backlog_por_status.columns:
            backlog_por_status[col] = 0  # Adiciona a coluna com valores zerados se não existir

    # Cores personalizadas para as linhas
    colors = ['blue', 'red', 'green']  # Cores para 'Concluido', 'Não' e 'Total'
    
    # Gráfico de linha mostrando concluído, não concluído e total
    fig_backlog_status = px.line(
        backlog_por_status,
        x='Backlog',
        y=['Resolvido', 'Pendente', 'Total'],
        labels={'Backlog': 'Mês/Ano', 'value': 'Contagem', 'variable': 'Status'},
        title="Distribuição de Incidentes por Status",
        markers=True,
        color_discrete_sequence=colors  # Aplicando as cores
    )

    # Adicionando rótulos de dados
    for col in ['Resolvido', 'Pendente','Total']:
        # Criar um Scatter separado para os rótulos de dados
        fig_backlog_status.add_trace(
            go.Scatter(
                x=backlog_por_status['Backlog'],
                y=backlog_por_status[col],
                mode='markers+text',  # Apenas marcadores e texto
                name=col,  # Nome para a legenda
                text=backlog_por_status[col].astype(str),  # Rótulos de dados
                textposition='top center',  # Posição do rótulo
                marker=dict(size=8),  # Tamanho dos marcadores
                showlegend=False  # Não mostrar na legenda
            )
        )

    fig_backlog_status.update_layout(
        xaxis_title="Mês/Ano",
        yaxis_title="Contagem",
        showlegend=True  # Habilita a legenda
    )
    
    st.plotly_chart(fig_backlog_status, use_container_width=True)


# Gráfico de Pizza: Distribuição Backlog Responsáveis
st.subheader("Distribuição Backlog Responsáveis")

if 'Responsavel' in df_filtrado.columns:
    df_status = df_filtrado['Responsavel'].value_counts()

    # Calcular porcentagens
    total = df_status.sum()
    percentages = df_status / total * 100

    # Agrupar valores menores que 5% em 'Outros' se houver
    df_status_grouped = df_status[percentages >= 5]
    other_count = df_status[percentages < 5].sum()

    # Adicionar 'Outros' apenas se houver valores menores que 5%
    if other_count > 0:
        df_status_grouped['Outros'] = other_count

    # Verificar se existem valores para plotar
    if not df_status_grouped.empty:
        # Gráfico de pizza
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

    # Calculando o percentual de resolvidos
    percent_resolved = (resolved_by_responsavel / df_responsavel) * 100

    # Criar DataFrame para plotar
    df_desempenho = pd.DataFrame({
        'Total': df_responsavel,
        'Resolvidos': resolved_by_responsavel,
        'Percentual Resolvidos': percent_resolved.fillna(0)
    }).reset_index()

    df_desempenho.columns = ['Responsável', 'Total', 'Resolvidos', 'Percentual Resolvidos']

    # Gráfico de barras
    fig_desempenho = go.Figure()

    # Total
    fig_desempenho.add_trace(go.Bar(
        x=df_desempenho['Responsável'],
        y=df_desempenho['Total'],
        name='Total',
        marker_color='lightblue',
        text=df_desempenho['Total'],  # Rótulo de dados
        textposition='auto'  # Posição automática dos rótulos
    ))

    # Resolvidos
    fig_desempenho.add_trace(go.Bar(
        x=df_desempenho['Responsável'],
        y=df_desempenho['Resolvidos'],
        name='Resolvidos',
        marker_color='lightgreen',
        text=df_desempenho['Resolvidos'],  # Rótulo de dados
        textposition='auto'  # Posição automática dos rótulos
    ))

    # Atualizando o layout do gráfico
    fig_desempenho.update_layout(
        title='Desempenho dos Responsáveis',
        xaxis_title='Responsável',
        yaxis_title='Quantidade',
        barmode='group',
        legend_title='Tipo'
    )

    # Adicionando percentual como texto nas barras "Resolvidos"
    for i in range(len(df_desempenho)):
        fig_desempenho.add_annotation(
            x=df_desempenho['Responsável'][i],
            y=df_desempenho['Resolvidos'][i],
            text=f"{df_desempenho['Percentual Resolvidos'][i]:.1f}%",
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-30,  # Distância do texto em relação à barra
            font=dict(size=10)
        )

    # Mostrando o gráfico no Streamlit
    st.plotly_chart(fig_desempenho, use_container_width=True)


    


import pandas as pd
import plotly.express as px
import streamlit as st

# Caminho para a planilha na pasta Base
file_path = 'Base/Backlog.xlsx'  # Ajuste conforme necessário

# Função para carregar os dados
def load_data():
    try:
        df = pd.read_excel(file_path)
        return df
    except FileNotFoundError:
        st.error(f"Arquivo não encontrado: {file_path}")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar o arquivo: {e}")
        return None

# Função para criar gráficos
def create_charts(df):
    st.title("Análise de Backlog")

    # Filtrando por tipo de projeto (SPN ou ITI)
    project_type = st.sidebar.selectbox("Selecione o tipo de projeto", ["SPN", "ITI"])
    filtered_df = df[df['Tipo'] == project_type]

    # Gráfico de pizza para responsáveis
    df_responsaveis = filtered_df['Responsavel'].value_counts().reset_index()
    df_responsaveis.columns = ['Responsavel', 'Count']
    
    if not df_responsaveis.empty:
        fig1 = px.pie(df_responsaveis, names='Responsavel', values='Count', 
                      title=f"Distribuição de Responsáveis - {project_type}", 
                      hole=0.3, 
                      labels={'Count': 'Contagem'})
        fig1.update_traces(textinfo='percent+label')
        st.plotly_chart(fig1, use_container_width=True)

    # Gráfico de barras para média de dias para resolução
    mean_days = filtered_df['Dias para Resolução'].mean()
    fig2 = px.bar(x=['Média Dias para Resolução'], y=[mean_days],
                  labels={'x': '', 'y': 'Dias'},
                  title=f"Média Dias para Resolução - {project_type}")
    fig2.update_traces(text=mean_days, textposition='auto')
    st.plotly_chart(fig2, use_container_width=True)

    # Gráfico de dispersão para mostrar a relação entre "Dias para Resolução" e "Complexidade"
    if 'Complexidade' in filtered_df.columns:
        fig3 = px.scatter(filtered_df, x='Complexidade', y='Dias para Resolução',
                          title=f"Relação entre Complexidade e Dias para Resolução - {project_type}",
                          labels={'Complexidade': 'Complexidade', 'Dias para Resolução': 'Dias'})
        st.plotly_chart(fig3, use_container_width=True)

def main():
    df = load_data()
    if df is not None:
        create_charts(df)

if __name__ == "__main__":
    main()

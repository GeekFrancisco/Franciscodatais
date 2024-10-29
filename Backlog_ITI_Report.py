import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# Função para ler o arquivo Excel e retornar um DataFrame
def ler_arquivo_excel(caminho, aba):
    try:
        df = pd.read_excel(caminho, sheet_name=aba)
        return df
    except FileNotFoundError:
        print(f"Erro: O arquivo '{caminho}' não foi encontrado.")
        exit()
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")
        exit()

# Função para calcular a diferença de meses entre a data atual e a data da coluna Backlog
def calcular_tempo(backlog_data):
    """Calcula a diferença em meses entre a data do backlog e a data atual."""
    if pd.isna(backlog_data):  # Verifica se o valor é NaN
        return None
    try:
        backlog_date = datetime.strptime(backlog_data, '%m/%y')
        data_atual = datetime.now()
        diferenca_meses = (data_atual.year - backlog_date.year) * 12 + (data_atual.month - backlog_date.month)
        return diferenca_meses
    except ValueError:
        return None

# Função para gerar o PDF
def gerar_pdf(df, colunas_desejadas, nome_arquivo, data_inicio, data_fim):
    pdf = FPDF()
    pdf.add_page()

    # Definindo margens
    pdf.set_margins(15, 15, 15)

    # Título
    pdf.set_font("Arial", 'B', size=16)
    pdf.cell(0, 10, txt=f"Relatório de Backlog - Semana de {data_inicio} até {data_fim} - ITI", ln=True, align='C')
    pdf.ln(5)

    # Cabeçalho
    pdf.set_font("Arial", 'B', size=12)
    pdf.set_fill_color(200, 220, 255)

    largura_celulas = (pdf.w - 30) / len(colunas_desejadas)
    for coluna in colunas_desejadas:
        pdf.cell(largura_celulas, 10, coluna, border=1, fill=True, align='C')
    pdf.ln()

    # Dados
    pdf.set_font("Arial", size=12)
    for index, row in df.iterrows():
        for item in row:
            pdf.cell(largura_celulas, 10, str(item), border=1, align='C')
        pdf.ln()

    # Salva o PDF
    pdf.output(nome_arquivo)
    print(f"PDF gerado com sucesso: {nome_arquivo}")

# Caminho para o arquivo Excel
caminho_arquivo = 'Base/Backlog_2.xlsx'
aba = 'ITI'

# Lê a planilha
df = ler_arquivo_excel(caminho_arquivo, aba)

# Definir quais colunas você deseja incluir no PDF
colunas_desejadas = ['Responsavel', 'Incidente', 'Backlog', 'Status']

# Verificar se todas as colunas desejadas estão presentes
for coluna in colunas_desejadas:
    if coluna not in df.columns:
        print(f"Coluna '{coluna}' não encontrada na planilha.")
        exit()

# Substituir "Não" por "Em aberto" na coluna 'Status'
df['Status'] = df['Status'].replace('Não', 'Em aberto')

# Filtra o DataFrame e aplica a formatação necessária
df_filtrado = df[colunas_desejadas]

# Converte a coluna 'Backlog' para um formato de data apropriado
df_filtrado['Backlog'] = pd.to_datetime(df_filtrado['Backlog'], format='%m/%y', errors='coerce')
df_filtrado['Backlog'] = df_filtrado['Backlog'].dt.strftime('%m/%y')

# Aplica a função de cálculo de tempo e renomeia a coluna
df_filtrado['Tempo (Meses)'] = df_filtrado['Backlog'].apply(calcular_tempo)

# Obtém a data de início e fim da semana
data_inicio = df['Inicio_Semana'].iloc[0]
data_fim = df['Final_Semana'].iloc[0]

# Formata as datas para exibir corretamente como string
data_inicio_formatada = data_inicio.strftime('%d/%m/%Y')
data_fim_formatada = data_fim.strftime('%d/%m/%Y')

# Obtém o diretório onde o arquivo Excel está localizado
diretorio_raiz = os.path.dirname(os.path.abspath(caminho_arquivo))

# Define o caminho do diretório "Relatorio"
diretorio_relatorio = os.path.join(diretorio_raiz, 'Relatorio')

# Verifica se o diretório "Relatorio" existe; se não, cria o diretório
if not os.path.exists(diretorio_relatorio):
    os.makedirs(diretorio_relatorio)

# Define o caminho completo para o arquivo PDF
caminho_arquivo_pdf = os.path.join(diretorio_relatorio, 'Report_ITI_Backlog_Semana_2.pdf')

# Gera o PDF
gerar_pdf(df_filtrado, colunas_desejadas + ['Tempo (Meses)'], caminho_arquivo_pdf, data_inicio_formatada, data_fim_formatada)

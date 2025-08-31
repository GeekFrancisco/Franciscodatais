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
    if pd.isna(backlog_data):
        return None
    try:
        backlog_date = datetime.strptime(backlog_data, '%m/%y')
        data_atual = datetime.now()
        diferenca_meses = (data_atual.year - backlog_date.year) * 12 + (data_atual.month - backlog_date.month)
        return diferenca_meses
    except ValueError:
        return None

# Função para gerar o PDF com estatísticas e destaque em vermelho para status "Pendente"
def gerar_pdf(df, colunas_desejadas, nome_arquivo, data_inicio, data_fim):
    pdf = FPDF()
    pdf.add_page()

    # Definindo margens
    pdf.set_margins(15, 15, 15)

    # Título
    pdf.set_font("Arial", 'B', size=16)
    pdf.cell(0, 10, txt=f"Relatório de Backlog - Semana de {data_inicio} até {data_fim} - SPN", ln=True, align='C')
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
        for i, item in enumerate(row):
            # Destaca o texto em vermelho se o status for "Pendente"
            if colunas_desejadas[i] == "Status" and item == "Pendente":
                pdf.set_text_color(255, 0, 0)  # Vermelho
            else:
                pdf.set_text_color(0, 0, 0)  # Preto
            pdf.cell(largura_celulas, 10, str(item), border=1, align='C')
        pdf.ln()

    # Estatísticas
    pdf.ln(10)
    pdf.set_font("Arial", 'B', size=14)
    pdf.cell(0, 10, txt="Resumo de Incidentes", ln=True, align='L')
    pdf.set_font("Arial", size=12)
    pdf.set_text_color(0, 0, 0)  # Volta ao preto para o resumo

    # Calcula o total de incidentes e o número de resolvidos e pendentes
    total_incidentes = len(df)
    resolvidos = df['Status'].value_counts().get('Resolvido', 0)
    pendentes = df['Status'].value_counts().get('Pendente', 0)
    porcentagem_resolvidos = (resolvidos / total_incidentes) * 100
    porcentagem_pendentes = (pendentes / total_incidentes) * 100

    # Insere as estatísticas no PDF
    pdf.cell(0, 10, f"Total de Incidentes: {total_incidentes}", ln=True)
    pdf.cell(0, 10, f"Incidentes Resolvidos: {resolvidos} ({porcentagem_resolvidos:.1f}%)", ln=True)
    pdf.cell(0, 10, f"Incidentes Pendentes: {pendentes} ({porcentagem_pendentes:.1f}%)", ln=True)
    pdf.ln(5)

    # Calcula incidentes por responsável e insere no PDF
    incidentes_por_responsavel = df.groupby(['Responsavel', 'Status']).size().unstack(fill_value=0)
    for responsavel, row in incidentes_por_responsavel.iterrows():
        total = row.sum()
        pendente = row.get('Pendente', 0)
        resolvido = row.get('Resolvido', 0)
        pdf.cell(0, 10, f"{responsavel}: {total} incidentes ({pendente} Pendentes, {resolvido} Resolvidos)", ln=True)

    # Salva o PDF
    pdf.output(nome_arquivo)
    print(f"PDF gerado com sucesso: {nome_arquivo}")

# Caminho para o arquivo Excel
caminho_arquivo = 'Base/Backlog_14.xlsx'
aba = 'SPN'

# Lê a planilha
df = ler_arquivo_excel(caminho_arquivo, aba)

# Define as colunas que você deseja incluir no PDF
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
data_inicio = pd.to_datetime(df['Inicio_Semana'].iloc[0], format='%d/%m/%Y')
data_fim = pd.to_datetime(df['Final_Semana'].iloc[0], format='%d/%m/%Y')

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
caminho_arquivo_pdf = os.path.join(diretorio_relatorio, 'Report_SPN_Backlog_Semana_14_2025.pdf')

# Gera o PDF com formatação em vermelho para "Pendentes"
gerar_pdf(df_filtrado, colunas_desejadas + ['Tempo (Meses)'], caminho_arquivo_pdf, data_inicio_formatada, data_fim_formatada)

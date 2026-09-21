
import pandas as pd
import os
import re

DIRETORIO_2025 = r'C:\Users\franciscoj\Python_Initial\Pyhton_Web\data\base\2025'

def extrair_numero(nome_arquivo):
    match = re.search(r'Backlog_(\d+)', nome_arquivo, re.IGNORECASE)
    return int(match.group(1)) if match else 0

arquivos = [f for f in os.listdir(DIRETORIO_2025) if f.startswith('Backlog_') and f.endswith('.xlsx')]
arquivos = sorted(arquivos, key=extrair_numero)

print(f"Arquivos: {len(arquivos)}")

# Escolher um incidente para rastrear (com base no output anterior)
# Incidente 319336 apareceu em SPN Backlog_1.xlsx
incidente_alvo = 319336

print(f"Rastreando incidente {incidente_alvo}...")

encontrado = []

for arquivo in arquivos:
    caminho = os.path.join(DIRETORIO_2025, arquivo)
    try:
        xls = pd.ExcelFile(caminho)
        for sheet in ['SPN', 'ITI']:
            if sheet in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet)
                
                # Normalizar nomes de colunas
                df.columns = df.columns.str.strip()
                
                if 'Incidente' in df.columns:
                    match = df[df['Incidente'] == incidente_alvo]
                    if not match.empty:
                        dados = match.iloc[0]
                        registro = {
                            'Arquivo': arquivo,
                            'Sheet': sheet,
                            'Incidente': dados['Incidente'],
                            'Backlog (Data?)': dados.get('Backlog'),
                            'Data (Criacao?)': dados.get('Data'),
                            'Status': dados.get('Status')
                        }
                        encontrado.append(registro)
                        print(f"  -> Encontrado em {arquivo} ({sheet}): Status={registro['Status']}, Data={registro['Data (Criacao?)']}, Backlog={registro['Backlog (Data?)']}")
    except Exception as e:
        pass

print("\n--- Análise de Deduplicação ---")
df_encontrado = pd.DataFrame(encontrado)
if not df_encontrado.empty:
    print(df_encontrado)
    
    # Simular deduplicação keep='last'
    dedup_last = df_encontrado.drop_duplicates(subset=['Incidente'], keep='last')
    print("\nDeduplicação (keep='last'):")
    print(dedup_last[['Arquivo', 'Status', 'Data (Criacao?)', 'Backlog (Data?)']])
    
    # Simular deduplicação keep='first'
    dedup_first = df_encontrado.drop_duplicates(subset=['Incidente'], keep='first')
    print("\nDeduplicação (keep='first'):")
    print(dedup_first[['Arquivo', 'Status', 'Data (Criacao?)', 'Backlog (Data?)']])
else:
    print("Incidente não encontrado em múltiplos arquivos (ou erro na leitura).")

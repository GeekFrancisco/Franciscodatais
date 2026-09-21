import pandas as pd
import os
import re
import warnings

# Suppress warnings from openpyxl and pandas FutureWarnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')
warnings.simplefilter(action='ignore', category=FutureWarning)

# Diretório onde as planilhas estão localizadas
diretorio = r'C:\Users\franciscoj\Python_Initial\Pyhton_Web\data\base'

# Lista dinâmica: encontra todos os arquivos Backlog_*.xlsx na pasta base
arquivos = [f for f in os.listdir(diretorio) if f.startswith('Backlog_') and f.endswith('.xlsx')]

# Função para extrair número do arquivo para ordenação
def extrair_numero(nome_arquivo):
    match = re.search(r'Backlog_(\d+)', nome_arquivo, re.IGNORECASE)
    return int(match.group(1)) if match else 0

# Ordenar arquivos numericamente
planilhas = sorted(arquivos, key=extrair_numero)

# Inclui Backlog.xlsx se existir
if os.path.exists(os.path.join(diretorio, 'Backlog.xlsx')):
    planilhas.insert(0, 'Backlog.xlsx')

print(f"Planilhas encontradas para processar: {planilhas}")

# Colunas padrão
colunas_padrao = [
    'Setor', 'Responsavel', 'Ano', 'Semana',
    'Inicio_Semana', 'Final_Semana', 'Incidente',
    'Backlog', 'Data', 'Status', 'Coordenador'
]

# DataFrames consolidados
df_spn_consolidado = pd.DataFrame(columns=colunas_padrao)
df_iti_consolidado = pd.DataFrame(columns=colunas_padrao)

# Função para formatar datas
def formatar_datas(df):
    for col, fmt in {
        'Inicio_Semana': '%d/%m/%Y',
        'Final_Semana': '%d/%m/%Y',
        'Data': '%d/%m/%Y'
    }.items():
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce').dt.strftime(fmt)
    return df

# Função para limpar colunas de strings
def limpar_colunas(df):
    for coluna in df.select_dtypes(include=['object']).columns:
        df[coluna] = (
            df[coluna].astype(str)
            .str.strip()
            .replace({r'[\n\t\r\x0b\x0c]': ''}, regex=True)
        )
    return df

def validar_planilha(caminho):
    """
    Valida se a planilha atende aos requisitos mínimos para consolidação.
    Retorna: (valido (bool), mensagens (list))
    """
    mensagens = []
    abas_encontradas = []
    
    if not os.path.exists(caminho):
        return False, [f"Arquivo não encontrado: {caminho}"]

    try:
        excel_file = pd.ExcelFile(caminho)
        sheet_names = excel_file.sheet_names
    except Exception as e:
        return False, [f"Erro crítico ao abrir arquivo: {str(e)}"]

    # Verifica abas necessárias
    tem_conteudo_util = False
    
    # Se não encontrou abas esperadas mas o arquivo abriu, pode ser erro de XML
    abas_esperadas = ['SPN', 'ITI']
    abas_presentes = [aba for aba in abas_esperadas if aba in sheet_names]
    
    if not abas_presentes:
        mensagens.append("⚠️ Nenhuma aba 'SPN' ou 'ITI' identificada pelo Python.")
        
        # Check for lock file
        nome_arquivo = os.path.basename(caminho)
        lock_file = os.path.join(os.path.dirname(caminho), f"~${nome_arquivo}")
        if os.path.exists(lock_file):
             mensagens.append(f"   🚨 ALERTA: Arquivo de bloqueio encontrado ('~${nome_arquivo}').")
             mensagens.append("   👉 O arquivo parece estar ABERTO no Excel. Feche-o e tente novamente.")
        else:
             mensagens.append("   DICA: O arquivo pode ter erros internos invisíveis.")
             mensagens.append("   SOLUÇÃO: Abra este arquivo no Excel, clique em 'Salvar' e feche. Tente novamente.")
        return False, mensagens

    for aba in abas_esperadas:
        if aba in sheet_names:
            try:
                # Leitura rápida apenas do cabeçalho para validar colunas
                df_header = pd.read_excel(excel_file, sheet_name=aba, nrows=1)
                df_header.columns = df_header.columns.str.strip()
                
                if 'Responsavel' not in df_header.columns:
                    mensagens.append(f"Aba '{aba}' existe mas não possui coluna 'Responsavel'.")
                else:
                    abas_encontradas.append(aba)
                    tem_conteudo_util = True
            except Exception as e:
                mensagens.append(f"Erro ao ler aba '{aba}': {str(e)}")
        else:
            mensagens.append(f"Aba '{aba}' ausente.")
    
    if not tem_conteudo_util:
        return False, mensagens + ["Nenhuma aba válida (SPN ou ITI) com as colunas corretas foi encontrada."]
    
    return True, abas_encontradas

# Função para consolidar dados de uma aba
def consolidar_aba(df_origem, df_destino):
    if 'Incidente' not in df_origem.columns:
        return df_destino

    # Ensure Incidente is string for consistent matching
    df_origem['Incidente'] = df_origem['Incidente'].astype(str)
    if not df_destino.empty:
        df_destino['Incidente'] = df_destino['Incidente'].astype(str)

    # 1. Update existing records
    # Identify records that are in both source and destination
    existing_mask = df_origem['Incidente'].isin(df_destino['Incidente'])
    existing_records = df_origem[existing_mask]
    
    # Iterate to update specific fields (mimicking original logic but slightly optimized)
    # Note: A bulk update would be faster but sticking to iteration for safety with existing logic
    for _, row in existing_records.iterrows():
        # Find index in destination
        idx = df_destino.index[df_destino['Incidente'] == row['Incidente']]
        if not idx.empty:
            idx = idx[0]
            # Update columns present in row
            for col in df_destino.columns:
                if col in row:
                    df_destino.at[idx, col] = row[col]

    # 2. Append new records
    new_mask = ~existing_mask
    new_records = df_origem[new_mask]
    
    if not new_records.empty:
        # Clean columns to match destination if needed, or just concat
        # Using concat directly avoids the FutureWarning about empty/NA entries 
        # that happens when appending row-by-row with dropna
        df_destino = pd.concat([df_destino, new_records], ignore_index=True)

    # 3. Mark resolved
    # Atualiza status para 'Resolvido' se sumiu da planilha atual
    incidentes_atuais = set(df_origem['Incidente'])
    incidentes_consolidados = set(df_destino['Incidente'])
    incidentes_sumiram = incidentes_consolidados - incidentes_atuais
    
    if incidentes_sumiram:
        df_destino.loc[df_destino['Incidente'].isin(incidentes_sumiram), 'Status'] = 'Resolvido'

    return df_destino

# Processa cada planilha
print("\n🔍 --- INICIANDO VALIDAÇÃO PRÉVIA ---")
arquivos_validos = []
erros_validacao = False

for planilha in planilhas:
    caminho = os.path.join(diretorio, planilha)
    print(f"Validando: {planilha}...", end=' ')
    
    valido, info = validar_planilha(caminho)
    
    if valido:
        print(f"✅ OK (Abas: {', '.join(info)})")
        arquivos_validos.append(caminho)
    else:
        print(f"❌ ERRO")
        for msg in info:
            print(f"   -> {msg}")
        erros_validacao = True

if erros_validacao:
    print("\n⛔ A consolidação foi INTERROMPIDA devido a erros de validação.")
    print("Corrija os arquivos listados acima e tente novamente.")
    exit(1)

print("\n🚀 Validação concluída com sucesso! Iniciando consolidação...")

for caminho in arquivos_validos:
    print(f"🔄 Processando: {os.path.basename(caminho)}")
    
    # Não precisamos mais checar existência ou try/except genérico aqui, pois já validamos
    excel_file = pd.ExcelFile(caminho)
    sheet_names = excel_file.sheet_names
    
    for aba, df_destino in [('SPN', df_spn_consolidado), ('ITI', df_iti_consolidado)]:
        try:
            if aba not in sheet_names:
                continue

            df = pd.read_excel(excel_file, sheet_name=aba)
            df.columns = df.columns.str.strip()
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df = formatar_datas(df)
            df = limpar_colunas(df)
            
            # Validação de coluna já feita na etapa anterior, mas mantemos para segurança na leitura completa
            if 'Responsavel' not in df.columns:
                continue

            print(f"   -> Consolidando '{aba}': {len(df)} registros.")
            df_destino = consolidar_aba(df, df_destino)

            if aba == 'SPN':
                df_spn_consolidado = df_destino
            else:
                df_iti_consolidado = df_destino

        except Exception as e:
            print(f"❌ Erro inesperado ao processar aba {aba} em {os.path.basename(caminho)}: {e}")

# Garantir colunas padronizadas
df_spn_consolidado = df_spn_consolidado.reindex(columns=colunas_padrao)
df_iti_consolidado = df_iti_consolidado.reindex(columns=colunas_padrao)

# Resetar índices
df_spn_consolidado.reset_index(drop=True, inplace=True)
df_iti_consolidado.reset_index(drop=True, inplace=True)

# Salvar Excel consolidado
output_path = os.path.join(diretorio, 'consolidado.xlsx')
try:
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df_spn_consolidado.to_excel(writer, sheet_name='SPN', index=False)
        df_iti_consolidado.to_excel(writer, sheet_name='ITI', index=False)
except Exception as e:
    print(f"Erro ao salvar arquivo consolidado: {e}")

# Confirmação
if os.path.exists(output_path):
    print(f"✅ Arquivo consolidado gerado com sucesso em: {output_path}")
else:
    print("❌ Falha ao gerar o arquivo consolidado.")

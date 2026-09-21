
import pandas as pd
import os
import re
import warnings

# Suppress warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')
warnings.simplefilter(action='ignore', category=FutureWarning)

# Configuração de Caminhos
DIRETORIO_2025 = r'C:\Users\franciscoj\Python_Initial\Pyhton_Web\data\base\2025'
ARQUIVO_SAIDA = os.path.join(DIRETORIO_2025, 'consolidado_2025_analise.xlsx')

def extrair_numero(nome_arquivo):
    match = re.search(r'Backlog_(\d+)', nome_arquivo, re.IGNORECASE)
    return int(match.group(1)) if match else 0

def analisar_2025():
    print(f"🔍 Iniciando análise de arquivos em: {DIRETORIO_2025}")
    
    if not os.path.exists(DIRETORIO_2025):
        print(f"❌ Diretório não encontrado: {DIRETORIO_2025}")
        return

    arquivos = [f for f in os.listdir(DIRETORIO_2025) if f.startswith('Backlog_') and f.endswith('.xlsx')]
    arquivos = sorted(arquivos, key=extrair_numero)
    
    print(f"📄 Arquivos encontrados ({len(arquivos)}): {arquivos}")
    
    dfs_spn = []
    dfs_iti = []
    
    colunas_padrao = [
        'Setor', 'Responsavel', 'Ano', 'Semana',
        'Inicio_Semana', 'Final_Semana', 'Incidente',
        'Backlog', 'Data', 'Status', 'Coordenador'
    ]

    for arquivo in arquivos:
        caminho_completo = os.path.join(DIRETORIO_2025, arquivo)
        print(f"Processing: {arquivo}...")
        
        try:
            xls = pd.ExcelFile(caminho_completo)
            
            # Processar SPN
            if 'SPN' in xls.sheet_names:
                df_spn = pd.read_excel(xls, sheet_name='SPN')
                # Normalizar colunas
                cols_validas = [c for c in colunas_padrao if c in df_spn.columns]
                df_spn = df_spn[cols_validas]
                df_spn['Arquivo_Origem'] = arquivo
                dfs_spn.append(df_spn)
            
            # Processar ITI
            if 'ITI' in xls.sheet_names:
                df_iti = pd.read_excel(xls, sheet_name='ITI')
                cols_validas = [c for c in colunas_padrao if c in df_iti.columns]
                df_iti = df_iti[cols_validas]
                df_iti['Arquivo_Origem'] = arquivo
                dfs_iti.append(df_iti)
                
        except Exception as e:
            print(f"⚠️ Erro ao processar {arquivo}: {e}")

    # Consolidação
    print("\n🔄 Consolidando dados...")
    df_spn_final = pd.concat(dfs_spn, ignore_index=True) if dfs_spn else pd.DataFrame(columns=colunas_padrao)
    df_iti_final = pd.concat(dfs_iti, ignore_index=True) if dfs_iti else pd.DataFrame(columns=colunas_padrao)
    
    # Consolidado Geral (Antes da Deduplicação)
    df_geral = pd.concat([df_spn_final, df_iti_final], ignore_index=True)
    
    # --- DEDUPLICAÇÃO ---
    print("\n🧹 Removendo duplicatas (mesmo número de Incidente em semanas diferentes)...")
    total_bruto = len(df_geral)
    
    # Identificar coluna de ID (Preferência: 'Incidente')
    coluna_id = 'Incidente' if 'Incidente' in df_geral.columns else 'Backlog'
    print(f"🔑 Usando coluna '{coluna_id}' como identificador único.")
    
    if coluna_id in df_geral.columns:
        # Limpeza prévia de IDs nulos
        df_geral = df_geral.dropna(subset=[coluna_id])
        df_geral = df_geral[df_geral[coluna_id].astype(str).str.strip() != '']
        
        # # Deduplicar mantendo o último (last)
        df_unicos = df_geral.drop_duplicates(subset=[coluna_id], keep='last').copy()
    else:
        print("⚠️ Coluna de ID não encontrada. Usando dados brutos.")
        df_unicos = df_geral.copy()

    # --- TRATAMENTO DE DATAS (CRIAÇÃO vs ATUALIZAÇÃO) ---
    # Coluna 'Backlog' parece conter a Data de Criação/Entrada
    if 'Backlog' in df_unicos.columns:
        df_unicos['Data_Criacao'] = pd.to_datetime(df_unicos['Backlog'], errors='coerce')
        df_unicos['Mes_Criacao'] = df_unicos['Data_Criacao'].dt.month_name()
        df_unicos['Mes_Num_Criacao'] = df_unicos['Data_Criacao'].dt.month
    
    # Coluna 'Data' ou 'Inicio_Semana' contém a Data do Relatório/Status
    if 'Data' in df_unicos.columns:
        df_unicos['Data_Status'] = pd.to_datetime(df_unicos['Data'], errors='coerce')
    elif 'Inicio_Semana' in df_unicos.columns:
        df_unicos['Data_Status'] = pd.to_datetime(df_unicos['Inicio_Semana'], errors='coerce', dayfirst=True)

    total_unicos = len(df_unicos)
    print(f"📉 Redução: {total_bruto} registros brutos -> {total_unicos} registros únicos (Incidentes Distintos).")

    print(f"\n🌍 VOLUME TOTAL DO ANO (CONSOLIDADO): {total_unicos} Chamados Únicos")
    
    if not df_unicos.empty and 'Setor' in df_unicos.columns:
        resumo_setor = df_unicos['Setor'].value_counts().reset_index()
        resumo_setor.columns = ['Setor', 'Qtd']
        resumo_setor['%'] = (resumo_setor['Qtd'] / total_unicos * 100).map('{:.1f}%'.format)
        print("\n🔹 Volume por Departamento:")
        print(resumo_setor.to_string(index=False))
        
        # Picos de Entrada (Baseado na Data de Criação - Coluna Backlog)
        if 'Mes_Criacao' in df_unicos.columns:
           print("\n📅 Picos de Entrada de Chamados (Top 3 Meses de Criação):")
           # Contar apenas meses válidos
           df_datas_validas = df_unicos.dropna(subset=['Mes_Criacao'])
           picos_entrada = df_datas_validas.groupby(['Mes_Num_Criacao', 'Mes_Criacao']).size().reset_index(name='Qtd')
           picos_entrada = picos_entrada.sort_values(by='Qtd', ascending=False).head(3)
           print(picos_entrada[['Mes_Criacao', 'Qtd']].to_string(index=False))
           
           # Verificar se há chamados de 2024 carregados em 2025
           chamados_2024 = df_datas_validas[df_datas_validas['Data_Criacao'].dt.year < 2025]
           if not chamados_2024.empty:
               print(f"\n⚠️ Nota: {len(chamados_2024)} chamados foram criados antes de 2025 (Carry-over).")

    # Função auxiliar para imprimir resumo por setor
    def imprimir_resumo(nome, df_raw):
        # Aplicar mesma lógica de deduplicação e datas
        if coluna_id in df_raw.columns:
             df_clean = df_raw.drop_duplicates(subset=[coluna_id], keep='last')
        else:
             df_clean = df_raw
        
        # Converter datas
        if 'Backlog' in df_clean.columns:
            df_clean['Data_Criacao'] = pd.to_datetime(df_clean['Backlog'], errors='coerce')
            df_clean['Mes_Criacao'] = df_clean['Data_Criacao'].dt.month_name()
            df_clean['Mes_Num_Criacao'] = df_clean['Data_Criacao'].dt.month

        total_dep = len(df_clean)
        print(f"\n📌 Análise: {nome}")
        print(f"   VOLUME TOTAL DO ANO: {total_dep} Chamados Únicos")
        
        if 'Mes_Criacao' in df_clean.columns:
            print("   \n📅 Maiores Picos de Entrada (Top 3 Meses):")
            df_valid = df_clean.dropna(subset=['Mes_Criacao'])
            por_mes = df_valid.groupby(['Mes_Num_Criacao', 'Mes_Criacao']).size().reset_index(name='Qtd')
            picos = por_mes.sort_values(by='Qtd', ascending=False).head(3)
            print(picos[['Mes_Criacao', 'Qtd']].to_string(index=False))

    imprimir_resumo("SPN (Sistemas)", df_spn_final)
    imprimir_resumo("ITI (Infraestrutura)", df_iti_final)
    
    # Exportar Excel
    print(f"\n💾 Salvando arquivo consolidado em: {ARQUIVO_SAIDA}")
    with pd.ExcelWriter(ARQUIVO_SAIDA, engine='openpyxl') as writer:
        # 1. Resumo Executivo (Novo)
        # Criando um DataFrame customizado para o resumo
        resumo_dados = {
            'Métrica': ['Total Chamados (Ano)', 'Departamento Mais Demandado', 'Mês de Maior Pico'],
            'Valor': [
                total_unicos, 
                f"{resumo_setor.iloc[0]['Setor']} ({resumo_setor.iloc[0]['%']})" if not resumo_setor.empty else "N/A",
                f"{picos_entrada.iloc[0]['Mes_Criacao']} ({picos_entrada.iloc[0]['Qtd']} chamados)" if 'picos_entrada' in locals() and not picos_entrada.empty else "N/A"
            ]
        }
        pd.DataFrame(resumo_dados).to_excel(writer, sheet_name='Resumo_Executivo', index=False)

        # 2. Dados Analíticos
        df_unicos.to_excel(writer, sheet_name='Dados_Unicos_Consolidados', index=False)
        
        if not df_unicos.empty and 'Setor' in df_unicos.columns:
             resumo_setor_excel = df_unicos['Setor'].value_counts().reset_index()
             resumo_setor_excel.columns = ['Setor', 'Qtd']
             resumo_setor_excel['%'] = (resumo_setor_excel['Qtd'] / total_unicos)
             resumo_setor_excel.to_excel(writer, sheet_name='Resumo_Geral_Setor', index=False)
        
        # 3. Picos de Entrada (Tabela Auxiliar)
        if 'picos_entrada' in locals() and not picos_entrada.empty:
            picos_entrada.to_excel(writer, sheet_name='Top_Meses_Demanda', index=False)

    print("✅ Processo concluído com sucesso!")

if __name__ == "__main__":
    analisar_2025()

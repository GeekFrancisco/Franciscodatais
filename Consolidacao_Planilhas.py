import pandas as pd
import os
import re

# Diretório onde as planilhas estão localizadas
diretorio = r'C:\Users\franciscoj\Python_Initial\Pyhton_Web\Base'

# Lista dinâmica das planilhas
planilhas = [f'Backlog_{i}.xlsx' for i in range(1, 44)]
# Inclui Backlog.xlsx se existir
if os.path.exists(os.path.join(diretorio, 'Backlog.xlsx')):
    planilhas.insert(0, 'Backlog.xlsx')

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

# Função para consolidar dados de uma aba
def consolidar_aba(df_origem, df_destino):
    if 'Incidente' not in df_origem.columns:
        return df_destino

    for _, novo in df_origem.iterrows():
        if df_destino.empty or novo['Incidente'] not in df_destino['Incidente'].values:
            novo_df = pd.DataFrame([novo]).dropna(axis=1, how='all')
            df_destino = pd.concat([df_destino, novo_df], ignore_index=True)
        else:
            idx = df_destino[df_destino['Incidente'] == novo['Incidente']].index[0]
            for col in df_destino.columns:
                if col in novo:
                    df_destino.at[idx, col] = novo[col]

    # Atualiza status para 'Resolvido' se sumiu da planilha atual
    incidentes_atuais = set(df_origem['Incidente'])
    incidentes_consolidados = set(df_destino['Incidente'])
    incidentes_sumiram = incidentes_consolidados - incidentes_atuais
    df_destino.loc[df_destino['Incidente'].isin(incidentes_sumiram), 'Status'] = 'Resolvido'

    return df_destino

# Processa cada planilha
for planilha in planilhas:
    caminho = os.path.join(diretorio, planilha)
    
    for aba, df_destino in [('SPN', df_spn_consolidado), ('ITI', df_iti_consolidado)]:
        try:
            df = pd.read_excel(caminho, sheet_name=aba)
            df.columns = df.columns.str.strip()
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df = formatar_datas(df)
            df = limpar_colunas(df)
            
            if 'Responsavel' not in df.columns:
                print(f"Aba {aba} no arquivo {planilha} não contém 'Responsavel'. Pulando...")
                continue

            df_destino = consolidar_aba(df, df_destino)

            if aba == 'SPN':
                df_spn_consolidado = df_destino
            else:
                df_iti_consolidado = df_destino

        except Exception as e:
            print(f"Erro ao processar aba {aba} do arquivo {planilha}: {e}")

# Garantir colunas padronizadas
df_spn_consolidado = df_spn_consolidado.reindex(columns=colunas_padrao)
df_iti_consolidado = df_iti_consolidado.reindex(columns=colunas_padrao)

# Resetar índices
df_spn_consolidado.reset_index(drop=True, inplace=True)
df_iti_consolidado.reset_index(drop=True, inplace=True)

# Salvar Excel consolidado
output_path = os.path.join(diretorio, 'consolidado.xlsx')
with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    df_spn_consolidado.to_excel(writer, sheet_name='SPN', index=False)
    df_iti_consolidado.to_excel(writer, sheet_name='ITI', index=False)

# Confirmação
if os.path.exists(output_path):
    print(f"✅ Arquivo consolidado gerado com sucesso em: {output_path}")
else:
    print("❌ Falha ao gerar o arquivo consolidado.")

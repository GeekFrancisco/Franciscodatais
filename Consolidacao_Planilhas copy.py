import pandas as pd
import os
import re

# Diretório onde as planilhas estão localizadas
diretorio = r'C:\Users\franciscoj\Python_Initial\Pyhton_Web\Base'

# Lista com os nomes das planilhas
planilhas = [ 
    'Backlog.xlsx','Backlog_2.xlsx','Backlog_3.xlsx','Backlog_4.xlsx','Backlog_5.xlsx',
    'Backlog_6.xlsx','Backlog_7.xlsx','Backlog_8.xlsx','Backlog_9.xlsx','Backlog_10.xlsx',
    'Backlog_11.xlsx','Backlog_12.xlsx','Backlog_13.xlsx','Backlog_14.xlsx','Backlog_15.xlsx',
    'Backlog_16.xlsx','Backlog_17.xlsx','Backlog_18.xlsx','Backlog_19.xlsx','Backlog_20.xlsx',
    'Backlog_21.xlsx','Backlog_22.xlsx','Backlog_23.xlsx','Backlog_24.xlsx','Backlog_25.xlsx',
    'Backlog_26.xlsx','Backlog_27.xlsx','Backlog_28.xlsx','Backlog_29.xlsx','Backlog_30.xlsx',
    'Backlog_31.xlsx','Backlog_32.xlsx','Backlog_33.xlsx','Backlog_34.xlsx','Backlog_35.xlsx',
    'Backlog_36.xlsx','Backlog_37.xlsx','Backlog_38.xlsx'
]

# DataFrames para consolidar histórico
df_spn_consolidado = pd.DataFrame(columns=['Setor','Responsavel','Ano','Semana','Inicio_Semana',
                                           'Final_Semana','Incidente','Backlog','Data','Status','Coordenador'])
df_iti_consolidado = pd.DataFrame(columns=['Setor','Responsavel','Ano','Semana','Inicio_Semana',
                                           'Final_Semana','Incidente','Backlog','Data','Status','Coordenador'])

# Função para formatar datas
def formatar_datas(df):
    for coluna in ['Inicio_Semana','Final_Semana','Data']:
        if coluna in df.columns:
            df[coluna] = pd.to_datetime(df[coluna], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y')
    if 'Backlog' in df.columns:
        df['Backlog'] = pd.to_datetime(df['Backlog'], dayfirst=True, errors='coerce').dt.strftime('%m/%Y')
    return df

# Função para limpar strings
def limpar_colunas(df):
    for coluna in df.select_dtypes(include=['object']).columns:
        df[coluna] = df[coluna].str.strip()
        df[coluna] = df[coluna].apply(lambda x: re.sub(r'[\n\t\r\x0b\x0c]', '', x) if isinstance(x, str) else x)
    return df

# Função para atualizar consolidado
def atualizar_consolidado(df, df_consolidado):
    for _, novo_incidente in df.iterrows():
        if df_consolidado.empty or novo_incidente['Incidente'] not in df_consolidado['Incidente'].values:
            # Adiciona novo incidente
            df_consolidado = pd.concat([df_consolidado, pd.DataFrame([novo_incidente])], ignore_index=True)
        else:
            # Atualiza incidente existente
            idx = df_consolidado[df_consolidado['Incidente'] == novo_incidente['Incidente']].index[0]
            for col in df_consolidado.columns:
                if col in novo_incidente:
                    df_consolidado.at[idx, col] = novo_incidente[col]

    # Marca como Resolvido os incidentes que sumiram nesta semana
    incidentes_atuais = set(df['Incidente'])
    incidentes_consolidados = set(df_consolidado['Incidente'])
    incidentes_sumiram = incidentes_consolidados - incidentes_atuais
    df_consolidado.loc[df_consolidado['Incidente'].isin(incidentes_sumiram), 'Status'] = 'Resolvido'
    
    return df_consolidado

# Ler todas as planilhas e consolidar histórico
for planilha in planilhas:
    caminho_completo = os.path.join(diretorio, planilha)
    
    for aba, df_consolidado in [('SPN', df_spn_consolidado), ('ITI', df_iti_consolidado)]:
        try:
            df = pd.read_excel(caminho_completo, sheet_name=aba)
            df.columns = df.columns.str.strip()
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            if 'Responsavel' not in df.columns:
                print(f"A coluna 'Responsavel' não foi encontrada na aba {aba} do arquivo {planilha}.")
                continue
            
            df = formatar_datas(df)
            df = limpar_colunas(df)
            
            df_consolidado = atualizar_consolidado(df, df_consolidado)
            
            if aba == 'SPN':
                df_spn_consolidado = df_consolidado
            else:
                df_iti_consolidado = df_consolidado
                
        except Exception as e:
            print(f"Erro ao processar a aba {aba} do arquivo {planilha}: {e}")

# Garantir ordem das colunas
colunas_ordem = ['Setor','Responsavel','Ano','Semana','Inicio_Semana','Final_Semana',
                 'Incidente','Backlog','Data','Status','Coordenador']

df_spn_consolidado = df_spn_consolidado[[c for c in colunas_ordem if c in df_spn_consolidado.columns]]
df_iti_consolidado = df_iti_consolidado[[c for c in colunas_ordem if c in df_iti_consolidado.columns]]

# Salvar consolidado em Excel
output_path = os.path.join(diretorio, 'consolidado.xlsx')
with pd.ExcelWriter(output_path) as writer:
    df_spn_consolidado.to_excel(writer, sheet_name='SPN', index=False)
    df_iti_consolidado.to_excel(writer, sheet_name='ITI', index=False)

print("Consolidação completa com histórico e status concluída com sucesso.")

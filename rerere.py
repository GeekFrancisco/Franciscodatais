import pandas as pd
import os

# Diretório onde as planilhas estão localizadas
diretorio = r'C:\Users\franciscoj\Python_Initial\Pyhton_Web\Base'

# Lista com os nomes das planilhas
planilhas = ['Backlog.xlsx', 'Backlog_2.xlsx', 'Backlog_3.xlsx', 'Backlog_4.xlsx']

# DataFrames para armazenar os dados consolidados das abas SPN e ITI
df_spn_consolidado = pd.DataFrame()
df_iti_consolidado = pd.DataFrame()

# Função para formatar as colunas de data conforme solicitado
def formatar_datas(df):
    df['Inicio_Semana'] = pd.to_datetime(df['Inicio_Semana']).dt.strftime('%d/%m/%Y')
    df['Final_Semana'] = pd.to_datetime(df['Final_Semana']).dt.strftime('%d/%m/%Y')
    df['Backlog'] = pd.to_datetime(df['Backlog']).dt.strftime('%m/%Y')
    df['Data'] = pd.to_datetime(df['Data']).dt.strftime('%d/%m/%Y')
    return df

# Loop para ler cada planilha e suas abas
for planilha in planilhas:
    # Monta o caminho completo do arquivo
    caminho_completo = os.path.join(diretorio, planilha)
    
    # Ler e consolidar a aba SPN
    df_spn = pd.read_excel(caminho_completo, sheet_name='SPN')
    df_spn = formatar_datas(df_spn)
    df_spn_consolidado = pd.concat([df_spn_consolidado, df_spn], ignore_index=True)
    
    # Ler e consolidar a aba ITI
    df_iti = pd.read_excel(caminho_completo, sheet_name='ITI')
    df_iti = formatar_datas(df_iti)
    df_iti_consolidado = pd.concat([df_iti_consolidado, df_iti], ignore_index=True)

# Salvar os DataFrames consolidados em uma nova planilha, com abas separadas para SPN e ITI
with pd.ExcelWriter(r'C:\Users\franciscoj\Python_Initial\Pyhton_Web\Base\consolidado.xlsx') as writer:
    df_spn_consolidado.to_excel(writer, sheet_name='SPN', index=False)
    df_iti_consolidado.to_excel(writer, sheet_name='ITI', index=False)

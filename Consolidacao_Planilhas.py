import pandas as pd
import os

# Diretório onde as planilhas estão localizadas
diretorio = r'C:\Users\franciscoj\Python_Initial\Pyhton_Web\Base'

# Lista com os nomes das planilhas
planilhas = ['Backlog.xlsx', 'Backlog_2.xlsx', 'Backlog_3.xlsx', 'Backlog_4.xlsx', 'Backlog_5.xlsx', 'Backlog_6.xlsx', 'Backlog_7.xlsx', 
             'Backlog_8.xlsx', 'Backlog_9.xlsx', 'Backlog_10.xlsx']

# DataFrames para armazenar os dados consolidados das abas SPN e ITI
df_spn_consolidado = pd.DataFrame(columns=['Setor', 'Responsavel', 'Semana', 'Inicio_Semana', 'Final_Semana', 'Incidente', 'Backlog', 'Data', 'Status'])
df_iti_consolidado = pd.DataFrame(columns=['Setor', 'Responsavel', 'Semana', 'Inicio_Semana', 'Final_Semana', 'Incidente', 'Backlog', 'Data', 'Status'])

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
    print(f'Colunas na aba SPN do arquivo {planilha}:', df_spn.columns)  # Verificar colunas
    df_spn = formatar_datas(df_spn)
    
    # Verifique se a coluna 'Incidente' existe
    if 'Incidente' in df_spn.columns:
        for _, novo_incidente in df_spn.iterrows():
            # Se o DataFrame estiver vazio, adiciona diretamente
            if df_spn_consolidado.empty or novo_incidente['Incidente'] not in df_spn_consolidado['Incidente'].values:
                df_spn_consolidado = pd.concat([df_spn_consolidado, pd.DataFrame([novo_incidente])], ignore_index=True)
            else:
                # Atualiza o status do incidente existente
                df_spn_consolidado.loc[df_spn_consolidado['Incidente'] == novo_incidente['Incidente'], 'Status'] = novo_incidente['Status']
    else:
        print(f"A coluna 'Incidente' não está presente na aba SPN do arquivo {planilha}.")
    
    # Ler e consolidar a aba ITI
    df_iti = pd.read_excel(caminho_completo, sheet_name='ITI')
    print(f'Colunas na aba ITI do arquivo {planilha}:', df_iti.columns)  # Verificar colunas
    df_iti = formatar_datas(df_iti)
    
    # Verifique se a coluna 'Incidente' existe
    if 'Incidente' in df_iti.columns:
        for _, novo_incidente in df_iti.iterrows():
            # Se o DataFrame estiver vazio, adiciona diretamente
            if df_iti_consolidado.empty or novo_incidente['Incidente'] not in df_iti_consolidado['Incidente'].values:
                df_iti_consolidado = pd.concat([df_iti_consolidado, pd.DataFrame([novo_incidente])], ignore_index=True)
            else:
                # Atualiza o status do incidente existente
                df_iti_consolidado.loc[df_iti_consolidado['Incidente'] == novo_incidente['Incidente'], 'Status'] = novo_incidente['Status']
    else:
        print(f"A coluna 'Incidente' não está presente na aba ITI do arquivo {planilha}.")

# Salvar os DataFrames consolidados em uma nova planilha, com abas separadas para SPN e ITI
with pd.ExcelWriter(r'C:\Users\franciscoj\Python_Initial\Pyhton_Web\Base\consolidado.xlsx') as writer:
    df_spn_consolidado.to_excel(writer, sheet_name='SPN', index=False)
    df_iti_consolidado.to_excel(writer, sheet_name='ITI', index=False)

# Exibir as colunas disponíveis após a consolidação
print("Colunas disponíveis na tabela SPN:", df_spn_consolidado.columns.tolist())
print("Colunas disponíveis na tabela ITI:", df_iti_consolidado.columns.tolist())

print("Consolidação concluída com sucesso.")

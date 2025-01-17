import pandas as pd
import os
import re

# Diretório onde as planilhas estão localizadas
diretorio = r'C:\Users\franciscoj\Python_Initial\Pyhton_Web\Base'

# Lista com os nomes das planilhas
planilhas = [ 'Backlog.xlsx','Backlog_2.xlsx']

# DataFrames para armazenar os dados consolidados das abas SPN e ITI
df_spn_consolidado = pd.DataFrame(columns=['Setor', 'Responsavel', 'Ano', 'Semana', 'Inicio_Semana', 'Final_Semana', 'Incidente', 'Backlog', 'Data', 'Status', 'Coordenador'])
df_iti_consolidado = pd.DataFrame(columns=['Setor', 'Responsavel', 'Ano', 'Semana', 'Inicio_Semana', 'Final_Semana', 'Incidente', 'Backlog', 'Data', 'Status', 'Coordenador'])

# Função para formatar as colunas de data conforme solicitado
def formatar_datas(df):
    df['Inicio_Semana'] = pd.to_datetime(df['Inicio_Semana'], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y')
    df['Final_Semana'] = pd.to_datetime(df['Final_Semana'], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y')
    df['Backlog'] = pd.to_datetime(df['Backlog'], dayfirst=True, errors='coerce').dt.strftime('%m/%Y')
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y')
    return df

# Função para limpar espaços extras e caracteres invisíveis em colunas do tipo object
def limpar_colunas(df):
    for coluna in df.select_dtypes(include=['object']).columns:
        df[coluna] = df[coluna].str.strip()  # Remove espaços extras no início e no final
        df[coluna] = df[coluna].apply(lambda x: re.sub(r'[\n\t\r\x0b\x0c]', '', x) if isinstance(x, str) else x)  # Remove caracteres invisíveis
    return df

# Loop para ler cada planilha e suas abas
for planilha in planilhas:
    # Monta o caminho completo do arquivo
    caminho_completo = os.path.join(diretorio, planilha)
    
    # Ler e consolidar a aba SPN
    try:
        df_spn = pd.read_excel(caminho_completo, sheet_name='SPN')
        print(f'Colunas na aba SPN do arquivo {planilha}:', df_spn.columns)  # Verificar colunas
        
        # Corrigir os nomes das colunas para garantir que 'Responsavel' exista
        df_spn.columns = df_spn.columns.str.strip()  # Remover espaços extras no nome das colunas
        if 'Responsavel' not in df_spn.columns:
            print("A coluna 'Responsavel' não foi encontrada na aba SPN.")
            continue  # Pula esta aba e continua com o próximo arquivo
        
        df_spn = formatar_datas(df_spn)
        df_spn = limpar_colunas(df_spn)  # Limpar colunas de texto
        
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
    except Exception as e:
        print(f"Erro ao processar a aba SPN do arquivo {planilha}: {e}")

    # Ler e consolidar a aba ITI
    try:
        df_iti = pd.read_excel(caminho_completo, sheet_name='ITI')
        print(f'Colunas na aba ITI do arquivo {planilha}:', df_iti.columns)  # Verificar colunas
        
        # Corrigir os nomes das colunas para garantir que 'Responsavel' exista
        df_iti.columns = df_iti.columns.str.strip()  # Remover espaços extras no nome das colunas
        if 'Responsavel' not in df_iti.columns:
            print("A coluna 'Responsavel' não foi encontrada na aba ITI.")
            continue  # Pula esta aba e continua com o próximo arquivo
        
        df_iti = formatar_datas(df_iti)
        df_iti = limpar_colunas(df_iti)  # Limpar colunas de texto
        
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
    except Exception as e:
        print(f"Erro ao processar a aba ITI do arquivo {planilha}: {e}")

# Reordenar as colunas para garantir que estão no mesmo formato em ambas as planilhas
df_spn_consolidado = df_spn_consolidado[[
    'Setor', 'Responsavel', 'Ano', 'Semana', 'Inicio_Semana', 'Final_Semana', 
    'Incidente', 'Backlog', 'Data', 'Status', 'Coordenador'
]]
df_iti_consolidado = df_iti_consolidado[[
    'Setor', 'Responsavel', 'Ano', 'Semana', 'Inicio_Semana', 'Final_Semana', 
    'Incidente', 'Backlog', 'Data', 'Status', 'Coordenador'
]]

# Salvar os DataFrames consolidados em uma nova planilha, com abas separadas para SPN e ITI
output_path = r'C:\Users\franciscoj\Python_Initial\Pyhton_Web\Base\consolidado.xlsx'
with pd.ExcelWriter(output_path) as writer:
    df_spn_consolidado.to_excel(writer, sheet_name='SPN', index=False)
    df_iti_consolidado.to_excel(writer, sheet_name='ITI', index=False)

# Exibir as colunas disponíveis após a consolidação
print("Colunas disponíveis na tabela SPN:", df_spn_consolidado.columns.tolist())
print("Colunas disponíveis na tabela ITI:", df_iti_consolidado.columns.tolist())

print("Consolidação concluída com sucesso.")

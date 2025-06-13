import pandas as pd
import os

diretorio = r'C:\Users\franciscoj\Python_Initial\Pyhton_Web\Base'
planilhas = [

             'Backlog.xlsx','Backlog_2.xlsx','Backlog_3.xlsx','Backlog_4.xlsx','Backlog_5.xlsx','Backlog_6.xlsx','Backlog_7.xlsx',
             'Backlog_8.xlsx','Backlog_9.xlsx','Backlog_10.xlsx','Backlog_11.xlsx','Backlog_12.xlsx','Backlog_13.xlsx','Backlog_14.xlsx',
             'Backlog_15.xlsx','Backlog_16.xlsx','Backlog_17.xlsx','Backlog_18.xlsx','Backlog_19.xlsx','Backlog_20.xlsx', 'Backlog_21.xlsx',
             'Backlog_22.xlsx','Backlog_23.xlsx'
        ]

resultados = []

for planilha in planilhas:
    caminho = os.path.join(diretorio, planilha)
    for aba in ['SPN', 'ITI']:
        try:
            df = pd.read_excel(caminho, sheet_name=aba)
            if 'Incidente' in df.columns:
                df['Arquivo'] = planilha
                df['Aba'] = aba
                resultados.append(df)
        except Exception as e:
            print(f"Erro ao ler {planilha} - {aba}: {e}")

if resultados:
    df_todos = pd.concat(resultados, ignore_index=True)
    df_todos['Semana'] = pd.to_numeric(df_todos['Semana'], errors='coerce')
    df_todos['Ano'] = pd.to_numeric(df_todos['Ano'], errors='coerce')
    df_todos['Mes'] = ((df_todos['Semana'] - 1) // 4 + 1).astype(int)
    df_todos = df_todos.drop_duplicates(subset=['Incidente', 'Ano', 'Semana'])

    # Encontrar incidentes em semanas consecutivas
    df_todos = df_todos.sort_values(['Incidente', 'Ano', 'Semana'])
    df_todos['Semana_Anterior'] = df_todos.groupby('Incidente')['Semana'].shift(1)
    df_todos['Ano_Anterior'] = df_todos.groupby('Incidente')['Ano'].shift(1)
    df_todos['Consecutivo'] = (
        ((df_todos['Ano'] == df_todos['Ano_Anterior']) & (df_todos['Semana'] == df_todos['Semana_Anterior'] + 1)) |
        ((df_todos['Ano'] == df_todos['Ano_Anterior'] + 1) & (df_todos['Semana'] == 1) & (df_todos['Semana_Anterior'] == 52))
    )

    # Selecionar apenas os incidentes que passaram de uma semana para outra
    df_consecutivos = df_todos[df_todos['Consecutivo']]

    if not df_consecutivos.empty:
        for (ano, mes), grupo in df_consecutivos.groupby(['Ano', 'Mes']):
            print(f"\nIncidentes com semanas consecutivas em {ano} - mês {mes}:")
            print(grupo[['Incidente', 'Responsavel', 'Semana', 'Status', 'Setor', 'Arquivo', 'Aba']].to_string(index=False))
    else:
        print("Nenhum incidente passou de uma semana para outra.")
else:
    print("Nenhum incidente encontrado em nenhuma planilha.")
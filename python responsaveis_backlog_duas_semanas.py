import pandas as pd
import os

diretorio = r'C:\Users\franciscoj\Python_Initial\Pyhton_Web\Base'
planilhas = [ 
             'Backlog.xlsx','Backlog_2.xlsx','Backlog_3.xlsx','Backlog_4.xlsx','Backlog_5.xlsx','Backlog_6.xlsx','Backlog_7.xlsx','Backlog_8.xlsx','Backlog_9.xlsx','Backlog_10.xlsx',
             'Backlog_11.xlsx','Backlog_12.xlsx','Backlog_13.xlsx','Backlog_14.xlsx','Backlog_15.xlsx','Backlog_16.xlsx','Backlog_17.xlsx','Backlog_18.xlsx','Backlog_19.xlsx','Backlog_20.xlsx',
             'Backlog_21.xlsx','Backlog_22.xlsx','Backlog_23.xlsx','Backlog_24.xlsx','Backlog_25.xlsx','Backlog_26.xlsx','Backlog_27.xlsx','Backlog_28.xlsx','Backlog_29.xlsx','Backlog_30.xlsx'
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

# ...existing code...
if resultados:
    df_todos = pd.concat(resultados, ignore_index=True)
    df_todos['Semana'] = pd.to_numeric(df_todos['Semana'], errors='coerce')
    df_todos['Ano'] = pd.to_numeric(df_todos['Ano'], errors='coerce')
    df_todos['Mes'] = ((df_todos['Semana'] - 1) // 4 + 1).astype(int)
    df_todos = df_todos.drop_duplicates(subset=['Incidente', 'Ano', 'Semana'])

    # Ordenar para facilitar o cálculo
    df_todos = df_todos.sort_values(['Incidente', 'Ano', 'Semana'])

    # Filtrar apenas pendentes
    df_pendentes = df_todos[df_todos['Status'].str.lower() == 'pendente']

    # Marcar sequência de semanas pendentes por incidente
    df_pendentes['Grupo'] = (
        (df_pendentes['Semana'] - df_pendentes.groupby('Incidente').cumcount())
    )

    # Agrupar por incidente e grupo para encontrar sequências
    sequencias = (
        df_pendentes.groupby(['Incidente', 'Grupo'])
        .filter(lambda x: len(x) >= 3)  # 3 ou mais semanas pendente
    )

    if not sequencias.empty:
        for (ano, mes), grupo in sequencias.groupby(['Ano', 'Mes']):
            print(f"\nIncidentes pendentes por 3 ou mais semanas consecutivas em {ano} - mês {mes}:")
            print(grupo[['Incidente', 'Responsavel', 'Semana', 'Status', 'Setor', 'Arquivo', 'Aba']].to_string(index=False))
    else:
        print("Nenhum incidente ficou pendente por mais de 2 semanas consecutivas.")
else:
    print("Nenhum incidente encontrado em nenhuma planilha.")
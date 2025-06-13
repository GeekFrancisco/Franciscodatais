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
    df_todos = df_todos.drop_duplicates(subset=['Incidente', 'Ano', 'Semana', 'Aba'])

    for aba, min_semanas in [('SPN', 3), ('ITI', 5)]:
        df_aba = df_todos[df_todos['Aba'] == aba].copy()
        df_aba = df_aba.sort_values(['Incidente', 'Ano', 'Semana'])
        # Calcular sequência de semanas consecutivas para cada incidente
        df_aba['Grupo'] = (
            (df_aba['Semana'] != df_aba.groupby('Incidente')['Semana'].shift(1) + 1) |
            (df_aba['Ano'] != df_aba.groupby('Incidente')['Ano'].shift(1))
        ).cumsum()
        df_aba['Seq'] = df_aba.groupby(['Incidente', 'Grupo']).cumcount() + 1

        # Filtrar incidentes com pelo menos min_semanas consecutivas
        incidentes_longos = df_aba[df_aba['Seq'] >= min_semanas]

        if not incidentes_longos.empty:
            print(f"\nIncidentes na aba {aba} com pelo menos {min_semanas} semanas consecutivas:")
            for (ano, mes), grupo in incidentes_longos.groupby(['Ano', 'Mes']):
                print(f"\nAno: {ano} - Mês: {mes}")
                print(grupo[['Incidente', 'Responsavel', 'Semana', 'Status', 'Setor', 'Arquivo', 'Aba']].to_string(index=False))
        else:
            print(f"\nNenhum incidente na aba {aba} ficou mais de {min_semanas * 7} dias (ou {min_semanas} semanas) consecutivos.")
else:
    print("Nenhum incidente encontrado em nenhuma planilha.")
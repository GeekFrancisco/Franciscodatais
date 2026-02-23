import pandas as pd
import os

diretorio = r'C:\Users\franciscoj\Python_Initial\Pyhton_Web\data\base'
planilhas = [ 
    'Backlog_1.xlsx','Backlog_2.xlsx','Backlog_3.xlsx','Backlog_4.xlsx',
]

resultados = []

for planilha in planilhas:
    caminho = os.path.join(diretorio, planilha)
    for aba in ['ITI']:
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
    # Garantir que as colunas de semana e ano são numéricas
    df_todos['Semana'] = pd.to_numeric(df_todos['Semana'], errors='coerce')
    df_todos['Ano'] = pd.to_numeric(df_todos['Ano'], errors='coerce')

    # Remover linhas com valores inválidos (NaN) em Semana ou Ano
    df_todos = df_todos.dropna(subset=['Semana', 'Ano'])

    # Criar coluna de mês para agrupamento (opcional)
    df_todos['Mes'] = ((df_todos['Semana'] - 1) // 4 + 1).astype(int)

    for aba in ['ITI']:
        min_semanas = 4  # 4 semanas = ~28 dias (aproximação de 30 dias)
        df_aba = df_todos[(df_todos['Aba'] == aba) & (df_todos['Status'].str.lower() == 'pendente')].copy()
        df_aba = df_aba.sort_values(['Incidente', 'Ano', 'Semana'])

        # Calcular sequência de semanas consecutivas para cada incidente
        df_aba['Grupo'] = (
            (df_aba['Semana'] != df_aba.groupby('Incidente')['Semana'].shift(1) + 1) |
            (df_aba['Ano'] != df_aba.groupby('Incidente')['Ano'].shift(1))
        ).cumsum()
        df_aba['Seq'] = df_aba.groupby(['Incidente', 'Grupo']).cumcount() + 1

        # Filtrar incidentes com pelo menos min_semanas consecutivas pendentes
        incidentes_longos = df_aba[df_aba['Seq'] >= min_semanas]

        if not incidentes_longos.empty:
            print(f"\nIncidentes na aba {aba} com mais de 30 dias (5 semanas) pendentes:")
            for (ano, mes), grupo in incidentes_longos.groupby(['Ano', 'Mes']):
                print(f"\nAno: {ano} - Mês: {mes}")
                print(grupo[['Incidente', 'Responsavel', 'Semana', 'Status', 'Setor', 'Arquivo', 'Aba']].to_string(index=False))
        else:
            print(f"\nNenhum incidente na aba {aba} ficou 4 semanas ou mais pendente.")
else:
    print("Nenhum dado encontrado nas planilhas.")
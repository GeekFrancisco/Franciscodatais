import pandas as pd
try:
    df = pd.read_excel('data/base/consolidado.xlsx')
    print("Colunas encontradas:")
    for col in df.columns:
        print(f"- {col}")
except Exception as e:
    print(e)

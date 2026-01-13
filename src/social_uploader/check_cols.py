import pandas as pd
try:
    df = pd.read_excel(r'c:\Users\franciscoj\Python_Initial\Pyhton_Web\src\video_generator\SHORTS\Roteiros\roteiro_versiculos.xlsx')
    print(df.columns.tolist())
    print(df.head(1))
except Exception as e:
    print(e)

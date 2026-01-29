import pandas as pd

excel_path = r'roteiros/Roteiro_Geral.xlsx'
try:
    df_dict = pd.read_excel(excel_path, sheet_name=None)
    if 'Shorts' in df_dict:
        # Corrige a linha 2 (índice 2, que é a linha 4 do Excel visualmente se contar cabeçalho)
        # O usuário confirmou que era a linha 4 no erro anterior
        df_dict['Shorts'].at[2, 'Idioma'] = 'EN'
        
        with pd.ExcelWriter(excel_path, engine='openpyxl', mode='w') as writer:
            for name, sheet in df_dict.items():
                sheet.to_excel(writer, sheet_name=name, index=False)
        print("Planilha corrigida com sucesso!")
    else:
        print("Aba Shorts não encontrada.")
except Exception as e:
    print(f"Erro: {e}")

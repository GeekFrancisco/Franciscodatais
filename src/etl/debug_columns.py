
import pandas as pd

file_path = r"C:\Users\franciscoj\Python_Initial\Pyhton_Web\data\base\2025\Backlog_1.xlsx"

try:
    print(f"Reading {file_path}...")
    xls = pd.ExcelFile(file_path)
    print(f"Sheet names: {xls.sheet_names}")
    
    for sheet in xls.sheet_names:
        if sheet in ['SPN', 'ITI']:
            df = pd.read_excel(xls, sheet_name=sheet, nrows=5)
            print(f"\n--- Sheet: {sheet} ---")
            print(df.columns.tolist())
            print(df[['Backlog', 'Incidente', 'Setor']].head())
except Exception as e:
    print(f"Error: {e}")

import os
import pandas as pd
import sys

# Ajusta path para importar settings
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

try:
    from configs.settings import EXCEL_PATH, INPUT_IMAGES_LONGS
except ImportError:
    # Fallback se a estrutura de pastas for diferente
    EXCEL_PATH = os.path.join(os.getcwd(), "Roteiros", "Roteiro_Geral.xlsx")
    INPUT_IMAGES_LONGS = os.path.join(os.getcwd(), "LONGOS", "input_images")

print(f"--- DIAGNÓSTICO DO GERADOR DE LONGOS ---")
print(f"1. Verificando Excel em: {EXCEL_PATH}")

if os.path.exists(EXCEL_PATH):
    print("   ✅ Arquivo Excel encontrado.")
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name=None)
        print(f"   📂 Abas encontradas: {list(df.keys())}")
        
        if 'Longos' in df:
            df_longos = df['Longos']
            print(f"   ✅ Aba 'Longos' encontrada com {len(df_longos)} linhas.")
            if len(df_longos) > 0:
                print("   📝 Primeiras linhas:")
                print(df_longos.head())
            else:
                print("   ⚠️ AVISO: A aba 'Longos' está vazia!")
        else:
            print("   ❌ ERRO: Aba 'Longos' NÃO encontrada no Excel.")
    except Exception as e:
        print(f"   ❌ ERRO ao ler Excel: {e}")
else:
    print("   ❌ ERRO: Arquivo Excel NÃO encontrado no caminho especificado.")
    # Tenta procurar na raiz para avisar o usuário
    root_excel = os.path.join(os.getcwd(), "Roteiro_Geral.xlsx")
    if os.path.exists(root_excel):
        print(f"   💡 DICA: Encontrei um 'Roteiro_Geral.xlsx' na raiz ({root_excel}). O script está procurando na pasta 'Roteiros'.")

print(f"\n2. Verificando Imagens em: {INPUT_IMAGES_LONGS}")
if os.path.exists(INPUT_IMAGES_LONGS):
    imgs = [f for f in os.listdir(INPUT_IMAGES_LONGS) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    if imgs:
        print(f"   ✅ Encontradas {len(imgs)} imagens: {imgs[:3]}...")
    else:
        print("   ❌ ERRO: Nenhuma imagem (.jpg, .png) encontrada na pasta.")
else:
    print("   ❌ ERRO: Pasta de imagens não encontrada.")

print("\n----------------------------------------")
import os
import sys
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
EXCEL_PATH = BASE_DIR / "roteiros" / "Roteiro_Geral.xlsx"
SHORTS_IMAGES_DIR = BASE_DIR / "SHORTS" / "input_images"
LONGOS_IMAGES_DIR = BASE_DIR / "LONGOS" / "input_images"


def validate_shorts(df: pd.DataFrame) -> bool:
    ok = True
    print("\n=== Validação da aba 'Shorts' ===")

    required_cols = ["Idioma", "Texto", "Titulo", "Imagem"]
    for col in required_cols:
        if col not in df.columns:
            print(f"ERRO: Coluna obrigatória ausente em 'Shorts': {col}")
            ok = False

    if not ok:
        return False

    for idx, row in df.iterrows():
        excel_row = idx + 2
        issues = []

        idioma = str(row.get("Idioma", "")).strip().upper()
        if idioma not in ("EN", "ES", "PT"):
            issues.append("Idioma inválido (esperado EN, ES ou PT)")

        texto = str(row.get("Texto", "")).strip()
        if not texto or texto.lower() == "nan":
            issues.append("Texto vazio ou inválido")
        elif len(texto.split()) < 3:
            issues.append("Texto muito curto (< 3 palavras)")

        titulo = str(row.get("Titulo", "")).strip()
        if not titulo or titulo.lower() == "nan":
            issues.append("Titulo vazio ou inválido")

        img_name = str(row.get("Imagem", "")).strip()
        if not img_name or img_name.lower() == "nan":
            issues.append("Imagem não preenchida")
        else:
            img_path = SHORTS_IMAGES_DIR / img_name
            if not img_path.exists():
                issues.append(f"Imagem '{img_name}' não encontrada em {SHORTS_IMAGES_DIR}")

        if issues:
            ok = False
            print(f"- Linha {excel_row} (Short):")
            for msg in issues:
                print(f"    • {msg}")

    if ok:
        print("Nenhum problema encontrado na aba 'Shorts'.")
    return ok


def validate_longos(df: pd.DataFrame) -> bool:
    ok = True
    print("\n=== Validação da aba 'Longos' ===")

    required_cols = ["Idioma", "Texto", "Titulo"]
    for col in required_cols:
        if col not in df.columns:
            print(f"ERRO: Coluna obrigatória ausente em 'Longos': {col}")
            ok = False

    if not ok:
        return False

    for idx, row in df.iterrows():
        excel_row = idx + 2
        issues = []

        idioma = str(row.get("Idioma", "")).strip().upper()
        if idioma not in ("EN", "ES", "PT"):
            issues.append("Idioma inválido (esperado EN, ES ou PT)")

        texto = str(row.get("Texto", "")).strip()
        if not texto or texto.lower() == "nan":
            issues.append("Texto vazio ou inválido")
        elif len(texto.split()) < 5:
            issues.append("Texto muito curto (< 5 palavras)")

        titulo = str(row.get("Titulo", "")).strip()
        if not titulo or titulo.lower() == "nan":
            issues.append("Titulo vazio ou inválido")

        tema_visual = str(row.get("TemaVisual", "")).strip()
        current_img_dir = LONGOS_IMAGES_DIR
        if tema_visual and tema_visual.lower() != "nan":
            possible_dir = LONGOS_IMAGES_DIR / tema_visual
            if possible_dir.exists():
                current_img_dir = possible_dir
            else:
                issues.append(f"TemaVisual '{tema_visual}' não encontrado em {LONGOS_IMAGES_DIR}")

        if not os.path.exists(current_img_dir):
            issues.append(f"Pasta de imagens não encontrada: {current_img_dir}")
        else:
            images = [
                f
                for f in os.listdir(current_img_dir)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))
            ]
            if not images:
                issues.append(f"Sem imagens válidas em {current_img_dir}")

        if issues:
            ok = False
            print(f"- Linha {excel_row} (Longo):")
            for msg in issues:
                print(f"    • {msg}")

    if ok:
        print("Nenhum problema encontrado na aba 'Longos'.")
    return ok


def main() -> None:
    if not EXCEL_PATH.exists():
        print(f"ERRO: Arquivo Excel não encontrado em {EXCEL_PATH}")
        sys.exit(1)

    try:
        sheets = pd.read_excel(EXCEL_PATH, sheet_name=None)
    except Exception as e:
        print(f"ERRO ao ler Excel: {e}")
        sys.exit(1)

    global_ok = True

    shorts_df = sheets.get("Shorts")
    if shorts_df is None:
        print("ERRO: Aba 'Shorts' não encontrada.")
        global_ok = False
    else:
        if not validate_shorts(shorts_df):
            global_ok = False

    longos_df = sheets.get("Longos")
    if longos_df is None:
        print("ERRO: Aba 'Longos' não encontrada.")
        global_ok = False
    else:
        if not validate_longos(longos_df):
            global_ok = False

    if global_ok:
        print("\n✅ Validação concluída: planilha pronta para gerar vídeos.")
        sys.exit(0)
    else:
        print("\n❌ Validação concluída: foram encontrados problemas na planilha.")
        sys.exit(1)


if __name__ == "__main__":
    main()


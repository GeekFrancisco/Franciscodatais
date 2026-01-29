import sys
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
EXCEL_PATH = BASE_DIR / "roteiros" / "Roteiro_Geral.xlsx"

REQUIRED_COLUMNS = [
    "Plataforma",
    "Publicar",
    "CanalDestino",
    "StatusPublicacao",
    "DataPublicacao",
    "HoraPublicacao",
    "GMT",
    "PalavraThumb",
    "TituloShort",
    "DescricaoShort",
    "Hashtags",
    "Privacidade",
    "PublicoInfantil",
    "YouTubeVideoId",
    "YouTubeURL",
]


def ensure_columns(df: pd.DataFrame):
    added = []

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            if col == "Plataforma":
                default = "YT"
            elif col == "Publicar":
                default = "NAO"
            elif col == "CanalDestino":
                default = ""
            elif col == "StatusPublicacao":
                default = "PENDENTE"
            elif col == "GMT":
                default = "-03:00"
            elif col == "Privacidade":
                default = "public"
            elif col == "PublicoInfantil":
                default = "NAO"
            else:
                default = ""
            df[col] = default
            added.append(col)

    if "Titulo" in df.columns and "TituloShort" in df.columns:
        mask = df["TituloShort"].isna() | (df["TituloShort"].astype(str).str.strip() == "")
        df.loc[mask, "TituloShort"] = df.loc[mask, "Titulo"].astype(str)

    if "Texto" in df.columns and "DescricaoShort" in df.columns:
        mask = df["DescricaoShort"].isna() | (df["DescricaoShort"].astype(str).str.strip() == "")
        df.loc[mask, "DescricaoShort"] = df.loc[mask, "Texto"].astype(str)

    existing = [c for c in df.columns if c not in REQUIRED_COLUMNS]
    ordered = existing + [c for c in REQUIRED_COLUMNS if c in df.columns]
    df = df[ordered]

    return df, added


def main() -> None:
    if not EXCEL_PATH.exists():
        print(f"ERRO: Arquivo Excel não encontrado em {EXCEL_PATH}")
        sys.exit(1)

    try:
        sheets = pd.read_excel(EXCEL_PATH, sheet_name=None)
    except Exception as e:
        print(f"ERRO ao ler Excel: {e}")
        sys.exit(1)

    updated_sheets = {}
    summary = {}

    for name, df in sheets.items():
        if name in ("Shorts", "Longos"):
            new_df, added = ensure_columns(df)
            updated_sheets[name] = new_df
            summary[name] = added
        else:
            updated_sheets[name] = df

    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="w") as writer:
        for name, df in updated_sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)

    print("✅ Atualização de colunas de publicação concluída.")
    for name in ("Shorts", "Longos"):
        if name in summary:
            if summary[name]:
                cols = ", ".join(summary[name])
                print(f"Aba '{name}': colunas adicionadas -> {cols}")
            else:
                print(f"Aba '{name}': nenhuma coluna nova adicionada.")


if __name__ == "__main__":
    main()


import pandas as pd
import os

INDICADOR_PATH = r"C:\Users\franciscoj\Python_Initial\Pyhton_Web\data\base\Indicador Backlog - ITI - SPN - TD - 2025.xlsx"


def parse_sheet(sheet_name: str):
    df_raw = pd.read_excel(INDICADOR_PATH, sheet_name=sheet_name, header=None, engine="openpyxl")
    if df_raw.empty:
        return None, None

    # Build multi-level headers from row 1 (months) and row 2 (subheaders)
    header_top = df_raw.iloc[1].tolist()
    header_sub = df_raw.iloc[2].tolist()

    columns = []
    current_top = None
    for i, (top, sub) in enumerate(zip(header_top, header_sub)):
        # Normalize headers
        if isinstance(top, str):
            top = top.strip()
        if isinstance(sub, str):
            sub = sub.strip()

        valid_top = top and isinstance(top, str) and top.lower() in {
            'janeiro','fevereiro','março','marco','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro','totais'
        }
        # Track merged headers: if top is a valid month/totais, set current_top
        if valid_top:
            current_top = top
            columns.append((top, sub or ''))
        else:
            # If this column belongs to the previously seen month/totais (merged cell), use current_top
            if current_top and isinstance(sub, str) and sub:
                columns.append((current_top, sub))
            else:
                # Leading columns like ID / Nome
                label = sub if isinstance(sub, str) and sub else (top if isinstance(top, str) and top else f"col_{i}")
                columns.append((label, ''))

    # Data begins after three header rows
    df = df_raw.iloc[3:].copy()
    # Assign multi-index-like tuples as columns joined by '|' to keep simple
    df.columns = [f"{a}|{b}" if b else a for a, b in columns]

    # Drop rows that are entirely NaN in relevant numeric columns
    df = df.dropna(how='all')
    return df, columns


def validate_sheet(sheet_name: str):
    df, columns = parse_sheet(sheet_name)
    if df is None:
        print(f"[WARN] Aba {sheet_name} vazia ou não pôde ser lida.")
        return []

    # Identify columns
    month_names = ['Janeiro','Fevereiro','Março','Marco','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
    backlog_cols = []
    lt30_cols = []
    total_backlog_col = None
    total_lt30_col = None

    for (top, sub) in columns:
        label = f"{top}|{sub}" if sub else top
        if isinstance(top, str) and top.strip() in month_names:
            if isinstance(sub, str):
                if 'backlog' in sub.lower():
                    backlog_cols.append(label)
                elif ('30' in sub.lower()) or ('15' in sub.lower()) or ('dias' in sub.lower()):
                    lt30_cols.append(label)
        elif isinstance(top, str) and top.strip().lower() == 'totais':
            if isinstance(sub, str):
                if 'backlog' in sub.lower():
                    total_backlog_col = label
                elif ('30' in sub.lower()) or ('15' in sub.lower()) or ('dias' in sub.lower()):
                    total_lt30_col = label

    # Fallback: detect ID/Nome columns for readability
    id_col = next((c for c in df.columns if isinstance(c, str) and c.strip().lower() in ['id','id|']), None)
    nome_col = next((c for c in df.columns if isinstance(c, str) and c.strip().lower() in ['nome','nome|']), None)

    # Convert numeric columns to numbers
    for col in backlog_cols + lt30_cols + [c for c in [total_backlog_col, total_lt30_col] if c]:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    # Compute sums across months and compare with Totais
    df['sum_backlog_meses'] = df[backlog_cols].sum(axis=1) if backlog_cols else 0
    df['sum_lt30_meses'] = df[lt30_cols].sum(axis=1) if lt30_cols else 0

    inconsistencies = []
    for idx, row in df.iterrows():
        nome = row.get(nome_col, '') if nome_col else ''
        rid = row.get(id_col, '') if id_col else ''
        total_b = row.get(total_backlog_col, None) if total_backlog_col else None
        total_l = row.get(total_lt30_col, None) if total_lt30_col else None

        if total_b is not None and row['sum_backlog_meses'] != total_b:
            inconsistencies.append({
                'ID': rid,
                'Nome': nome,
                'tipo': 'Backlog',
                'soma_meses': int(row['sum_backlog_meses']),
                'total_planilha': int(total_b)
            })
        if total_l is not None and row['sum_lt30_meses'] != total_l:
            inconsistencies.append({
                'ID': rid,
                'Nome': nome,
                'tipo': '<30 Dias',
                'soma_meses': int(row['sum_lt30_meses']),
                'total_planilha': int(total_l)
            })

    print(f"\nAba {sheet_name}:")
    print(f"- Meses (Backlog): {len(backlog_cols)} colunas")
    print(f"- Meses (<30 Dias): {len(lt30_cols)} colunas")
    print(f"- Totais presentes: Backlog? {'sim' if total_backlog_col else 'não'} | <30 Dias? {'sim' if total_lt30_col else 'não'}")
    if inconsistencies:
        print(f"- Inconsistências encontradas: {len(inconsistencies)}")
        for inc in inconsistencies[:20]:  # limitar saída
            print(f"  ID={inc['ID']} Nome={inc['Nome']} tipo={inc['tipo']} soma_meses={inc['soma_meses']} total_planilha={inc['total_planilha']}")
    else:
        print("- Nenhuma inconsistência de totais vs soma dos meses detectada.")
    # Return inconsistencies list for potential export
    for inc in inconsistencies:
        inc['Aba'] = sheet_name
    return inconsistencies


if __name__ == "__main__":
    if not os.path.exists(INDICADOR_PATH):
        print("Arquivo de indicadores não encontrado:", INDICADOR_PATH)
        raise SystemExit(1)
    all_incs = []
    for sheet in ['SPN', 'ITI']:
        res = validate_sheet(sheet)
        all_incs.extend(res)
    # Export to CSV if any inconsistencies
    if all_incs:
        out_path = os.path.join(os.path.dirname(INDICADOR_PATH), 'indicador_inconsistencias.csv')
        pd.DataFrame(all_incs).to_csv(out_path, index=False, encoding='utf-8-sig')
        print(f"\nRelatório de inconsistências salvo em: {out_path}")
    else:
        print("\nNenhuma inconsistência encontrada nas abas SPN e ITI.")
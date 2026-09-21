import argparse
import os
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-dir",
        default=r"C:\Users\franciscoj\Python_Initial\Pyhton_Web\data\base",
    )
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=28)
    parser.add_argument(
        "--out-excel",
        default=None,
    )
    parser.add_argument(
        "--out-html",
        default=None,
    )
    return parser.parse_args()


def normalizar_status(valor):
    if pd.isna(valor):
        return ""
    s = str(valor).strip().lower()
    if "resol" in s:
        return "Resolvido"
    if "pend" in s:
        return "Pendente"
    return str(valor).strip()


def to_datetime_safe(series):
    return pd.to_datetime(series, dayfirst=True, errors="coerce")


def ler_aba(caminho, aba, arquivo_num):
    df = pd.read_excel(caminho, sheet_name=aba)
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]
    df["Arquivo"] = Path(caminho).name
    df["Arquivo_Num"] = arquivo_num
    df["Aba"] = aba
    if "Status" in df.columns:
        df["Status"] = df["Status"].apply(normalizar_status)
    for col in ["Inicio_Semana", "Final_Semana", "Data", "Backlog"]:
        if col in df.columns:
            df[col] = to_datetime_safe(df[col])
    if "Semana" in df.columns:
        df["Semana"] = pd.to_numeric(df["Semana"], errors="coerce")
    if "Ano" in df.columns:
        df["Ano"] = pd.to_numeric(df["Ano"], errors="coerce")
    if "Incidente" in df.columns:
        df["Incidente"] = df["Incidente"].astype(str).str.strip()
        df = df[df["Incidente"].ne("") & df["Incidente"].ne("nan")]
    return df


def listar_planilhas(base_dir, start, end):
    encontrados = []
    faltando = []
    for n in range(start, end + 1):
        nome = f"Backlog_{n}.xlsx"
        caminho = os.path.join(base_dir, nome)
        if os.path.exists(caminho):
            encontrados.append(caminho)
        else:
            faltando.append(nome)
    return encontrados, faltando


def build_resumo_semana_setor(df_all):
    cols = {"Setor", "Ano", "Semana", "Incidente", "Status"}
    if not cols.issubset(df_all.columns):
        return pd.DataFrame()

    df = df_all.copy()
    df["Setor"] = df["Setor"].astype(str).str.strip().str.upper()
    df["Semana"] = pd.to_numeric(df["Semana"], errors="coerce")
    df["Ano"] = pd.to_numeric(df["Ano"], errors="coerce")
    df = df.dropna(subset=["Semana", "Ano", "Setor"])

    total = (
        df.groupby(["Setor", "Ano", "Semana"], as_index=False)["Incidente"]
        .nunique()
        .rename(columns={"Incidente": "Total"})
    )

    pend = (
        df[df["Status"] != "Resolvido"]
        .groupby(["Setor", "Ano", "Semana"], as_index=False)["Incidente"]
        .nunique()
        .rename(columns={"Incidente": "Pendentes"})
    )

    resol = (
        df[df["Status"] == "Resolvido"]
        .groupby(["Setor", "Ano", "Semana"], as_index=False)["Incidente"]
        .nunique()
        .rename(columns={"Incidente": "Resolvidos"})
    )

    out = total.merge(pend, on=["Setor", "Ano", "Semana"], how="left").merge(
        resol, on=["Setor", "Ano", "Semana"], how="left"
    )
    out["Pendentes"] = out["Pendentes"].fillna(0).astype(int)
    out["Resolvidos"] = out["Resolvidos"].fillna(0).astype(int)
    out["Total"] = out["Total"].fillna(0).astype(int)
    out = out.sort_values(["Ano", "Semana", "Setor"]).reset_index(drop=True)
    return out


def build_top_responsaveis_semana_atual(df_all, top_n=10):
    needed = {"Setor", "Semana", "Ano", "Status", "Responsavel", "Incidente"}
    if not needed.issubset(df_all.columns):
        return pd.DataFrame()

    df = df_all.copy()
    df["Setor"] = df["Setor"].astype(str).str.strip().str.upper()
    df["Semana"] = pd.to_numeric(df["Semana"], errors="coerce")
    df["Ano"] = pd.to_numeric(df["Ano"], errors="coerce")
    df = df.dropna(subset=["Semana", "Ano", "Setor"])

    latest_per_setor = (
        df.groupby("Setor")[["Ano", "Semana"]]
        .max()
        .reset_index()
        .rename(columns={"Ano": "Ano_Latest", "Semana": "Semana_Latest"})
    )
    df = df.merge(latest_per_setor, on="Setor", how="left")
    df = df[(df["Ano"] == df["Ano_Latest"]) & (df["Semana"] == df["Semana_Latest"])]
    df = df[df["Status"] != "Resolvido"]
    df["Responsavel"] = df["Responsavel"].astype(str).str.strip()

    out = (
        df.groupby(["Setor", "Ano", "Semana", "Responsavel"], as_index=False)["Incidente"]
        .nunique()
        .rename(columns={"Incidente": "Pendentes"})
    )
    out = out.sort_values(["Setor", "Pendentes"], ascending=[True, False])
    out = out.groupby("Setor").head(top_n).reset_index(drop=True)
    return out


def grafico_tendencia(resumo):
    if resumo.empty:
        return go.Figure()

    fig = go.Figure()
    for setor, g in resumo.groupby("Setor"):
        g = g.sort_values(["Ano", "Semana"]).copy()
        g["Semana_Label"] = g.apply(lambda r: f"{int(r['Ano'])}-W{int(r['Semana']):02d}", axis=1)
        g["MovAvg"] = g["Total"].rolling(3, min_periods=1).mean()

        fig.add_trace(
            go.Scatter(
                x=g["Semana_Label"],
                y=g["Total"],
                mode="lines+markers",
                name=f"{setor} (Total)",
                line=dict(width=3),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=g["Semana_Label"],
                y=g["MovAvg"],
                mode="lines",
                name=f"{setor} (Média 3)",
                line=dict(width=2, dash="dash"),
                opacity=0.7,
            )
        )

    fig.update_layout(
        title="Evolução do Backlog (Total por Semana)",
        xaxis_title="Semana",
        yaxis_title="Qtd. de Incidentes (únicos por semana)",
        template="plotly_white",
        legend_title="Setor",
        height=520,
        margin=dict(l=30, r=30, t=70, b=30),
    )
    return fig


def grafico_status(resumo):
    if resumo.empty:
        return go.Figure()

    setores = list(resumo["Setor"].unique())
    setores = sorted(setores)
    fig = make_subplots(
        rows=len(setores),
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=[f"{s} - Pendentes x Resolvidos" for s in setores],
    )

    for i, setor in enumerate(setores, start=1):
        g = resumo[resumo["Setor"] == setor].sort_values(["Ano", "Semana"]).copy()
        g["Semana_Label"] = g.apply(lambda r: f"{int(r['Ano'])}-W{int(r['Semana']):02d}", axis=1)
        fig.add_trace(
            go.Bar(x=g["Semana_Label"], y=g["Pendentes"], name="Pendentes", marker_color="#C73E1D"),
            row=i,
            col=1,
        )
        fig.add_trace(
            go.Bar(x=g["Semana_Label"], y=g["Resolvidos"], name="Resolvidos", marker_color="#2ECC71"),
            row=i,
            col=1,
        )

    fig.update_layout(
        barmode="stack",
        title="Backlog por Semana (Status)",
        template="plotly_white",
        height=360 * len(setores),
        margin=dict(l=30, r=30, t=70, b=30),
    )
    return fig


def grafico_top_responsaveis(top_df):
    if top_df.empty:
        return go.Figure()

    setores = sorted(top_df["Setor"].unique())
    fig = make_subplots(
        rows=1,
        cols=len(setores),
        subplot_titles=[f"{s} - Top Pendentes (semana atual)" for s in setores],
        horizontal_spacing=0.08,
    )

    for i, setor in enumerate(setores, start=1):
        g = top_df[top_df["Setor"] == setor].sort_values("Pendentes", ascending=True)
        fig.add_trace(
            go.Bar(
                x=g["Pendentes"],
                y=g["Responsavel"],
                orientation="h",
                marker_color="#2E86AB" if setor == "SPN" else "#A23B72",
                name=setor,
            ),
            row=1,
            col=i,
        )

    fig.update_layout(
        title="Maiores responsáveis por pendências (semana mais recente por setor)",
        template="plotly_white",
        height=520,
        showlegend=False,
        margin=dict(l=30, r=30, t=70, b=30),
    )
    return fig


def gerar_html(out_path, titulo, kpis, figs):
    parts = []
    parts.append("<html><head><meta charset='utf-8'><title>")
    parts.append(titulo)
    parts.append("</title></head><body style='font-family: Arial, sans-serif; margin: 24px;'>")
    parts.append(f"<h1 style='margin-bottom: 6px;'>{titulo}</h1>")
    parts.append(f"<div style='color: #555; margin-bottom: 18px;'>Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>")
    parts.append("<div style='display:flex; gap:12px; flex-wrap:wrap; margin-bottom: 18px;'>")
    for label, value in kpis.items():
        parts.append(
            f"<div style='border: 1px solid #eee; border-radius: 10px; padding: 12px 14px; min-width: 220px; background: #fafafa;'>"
            f"<div style='font-size: 12px; color:#666; text-transform: uppercase; letter-spacing: .04em;'>{label}</div>"
            f"<div style='font-size: 22px; font-weight: 700; margin-top: 6px; color:#222;'>{value}</div>"
            f"</div>"
        )
    parts.append("</div>")

    include_plotly = True
    for fig in figs:
        parts.append(fig.to_html(full_html=False, include_plotlyjs="cdn" if include_plotly else False))
        include_plotly = False

    parts.append("</body></html>")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text("".join(parts), encoding="utf-8")


def main():
    args = parse_args()
    base_dir = args.base_dir

    planilhas, faltando = listar_planilhas(base_dir, args.start, args.end)
    if not planilhas:
        raise SystemExit("Nenhuma planilha encontrada no intervalo informado.")

    pattern = re.compile(r"Backlog_(\d+)\.xlsx$", re.IGNORECASE)
    dados = []
    for caminho in planilhas:
        nome = Path(caminho).name
        m = pattern.search(nome)
        arquivo_num = int(m.group(1)) if m else None
        for aba in ["SPN", "ITI"]:
            try:
                dados.append(ler_aba(caminho, aba, arquivo_num))
            except Exception:
                continue

    df_all = pd.concat(dados, ignore_index=True) if dados else pd.DataFrame()
    if df_all.empty:
        raise SystemExit("Não foi possível ler dados das abas SPN/ITI nas planilhas selecionadas.")

    df_all = df_all.loc[:, ~df_all.columns.duplicated()].copy()

    resumo = build_resumo_semana_setor(df_all)
    top_resp = build_top_responsaveis_semana_atual(df_all, top_n=10)

    total_linhas = len(df_all)
    total_unicos = df_all["Incidente"].nunique() if "Incidente" in df_all.columns else 0
    kpis = {
        "Planilhas (encontradas)": f"{len(planilhas)} (Backlog_{args.start} a Backlog_{args.end})",
        "Planilhas (faltando)": ", ".join(faltando) if faltando else "0",
        "Linhas (raw)": f"{total_linhas:,}".replace(",", "."),
        "Incidentes únicos (raw)": f"{total_unicos:,}".replace(",", "."),
    }

    fig1 = grafico_tendencia(resumo)
    fig2 = grafico_status(resumo)
    fig3 = grafico_top_responsaveis(top_resp)

    out_excel = args.out_excel
    if not out_excel:
        out_excel = os.path.join(base_dir, f"compilado_backlog_{args.start:02d}_{args.end:02d}.xlsx")

    out_html = args.out_html
    if not out_html:
        out_html = os.path.join(base_dir, "Relatorio", f"compilado_backlog_{args.start:02d}_{args.end:02d}.html")

    with pd.ExcelWriter(out_excel, engine="openpyxl") as writer:
        df_all.to_excel(writer, sheet_name="raw", index=False)
        resumo.to_excel(writer, sheet_name="resumo_semana_setor", index=False)
        top_resp.to_excel(writer, sheet_name="top_responsaveis", index=False)

    gerar_html(out_html, "Compilado Backlog (Backlog_01 a Backlog_28)", kpis, [fig1, fig2, fig3])

    print("OK")
    print("Excel:", out_excel)
    print("HTML :", out_html)


if __name__ == "__main__":
    main()


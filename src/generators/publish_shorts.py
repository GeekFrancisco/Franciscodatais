import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from src.configs.settings import EXCEL_PATH, OUTPUT_SHORTS


BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SECRETS_DIR = BASE_DIR / "secrets"
TOKENS_DIR = BASE_DIR / "tokens"
LOGS_DIR = BASE_DIR / "logs"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

REQUIRED_COLUMNS = [
    "Plataforma",
    "Publicar",
    "StatusPublicacao",
    "DataPublicacao",
    "HoraPublicacao",
    "GMT",
    "TituloShort",
    "DescricaoShort",
    "Hashtags",
    "Privacidade",
    "PublicoInfantil",
    "YouTubeVideoId",
    "YouTubeURL",
]


def get_token_filename(channel_code: str) -> str:
    code = (channel_code or "").strip().upper()
    if code == "ES":
        return "youtube_es.json"
    if code in ("EN", "EM"):
        return "youtube_en.json"
    if code == "TESTE":
        return "youtube_teste.json"
    return "youtube_default.json"


def build_publish_at(row: pd.Series) -> str | None:
    data_raw = row.get("DataPublicacao")
    hora_raw = row.get("HoraPublicacao")

    if pd.isna(data_raw) or pd.isna(hora_raw):
        return None

    try:
        if isinstance(data_raw, (pd.Timestamp, datetime)):
            data = data_raw.date()
        else:
            data = pd.to_datetime(str(data_raw), dayfirst=True).date()

        if isinstance(hora_raw, (pd.Timestamp, datetime)):
            hora = hora_raw.time()
        else:
            hora = pd.to_datetime(str(hora_raw)).time()
    except Exception:
        return None

    gmt_raw = str(row.get("GMT") or "").strip()
    offset_hours = -3
    offset_minutes = 0

    if gmt_raw:
        s = gmt_raw.replace("UTC", "").replace("utc", "").strip()
        s = s.replace(" ", "")
        try:
            if ":" in s:
                if s[0].isdigit():
                    s = "+" + s
                sign = -1 if s[0] == "-" else 1
                parts = s[1:].split(":")
                h = int(parts[0])
                m = int(parts[1]) if len(parts) > 1 else 0
                offset_hours = sign * h
                offset_minutes = sign * m
            else:
                val = int(s)
                offset_hours = val
                offset_minutes = 0
        except Exception:
            pass

    tz = timezone(timedelta(hours=offset_hours, minutes=offset_minutes))
    dt_local = datetime(
        data.year,
        data.month,
        data.day,
        hora.hour,
        hora.minute,
        hora.second,
        tzinfo=tz,
    )
    return dt_local.isoformat(timespec="seconds")


def get_youtube_service(channel_code: str):
    client_secret_file = SECRETS_DIR / "client_secret_youtube.json"
    if not client_secret_file.exists():
        raise FileNotFoundError(f"Arquivo de credenciais não encontrado em {client_secret_file}")

    TOKENS_DIR.mkdir(parents=True, exist_ok=True)
    token_path = TOKENS_DIR / get_token_filename(channel_code)

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_file), SCOPES)
        creds = flow.run_local_server(port=0, prompt="consent")
        with open(token_path, "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def build_video_path_short(row: pd.Series, output_dir: Path) -> Path:
    idioma = str(row.get("Idioma", "")).strip().upper()
    img_name = str(row.get("Imagem", "")).strip()
    titulo = str(row.get("TituloShort") or row.get("Titulo") or "").strip()

    img_base = os.path.splitext(os.path.basename(img_name))[0]
    safe_img_name = "".join([c for c in img_base if c.isalnum() or c in (" ", "_")]).strip().replace(" ", "_")
    safe_title = "".join([c for c in titulo if c.isalnum() or c in (" ", "_")]).strip().replace(" ", "_")

    filename = f"{idioma}_{safe_img_name}_{safe_title}.mp4"
    return Path(OUTPUT_SHORTS) / filename


def build_metadata(row: pd.Series) -> dict:
    titulo = str(row.get("TituloShort") or row.get("Titulo") or "").strip()
    descricao_base = str(row.get("DescricaoShort") or "").strip()
    hashtags = str(row.get("Hashtags") or "").strip()

    if descricao_base and hashtags:
        descricao = f"{descricao_base}\n\n{hashtags}"
    elif hashtags:
        descricao = hashtags
    else:
        descricao = descricao_base

    privacidade = str(row.get("Privacidade") or "public").strip().lower()

    publico_infantil_raw = str(row.get("PublicoInfantil") or "NAO").strip().upper()
    if publico_infantil_raw == "NÃO":
        publico_infantil_raw = "NAO"

    publico_infantil = publico_infantil_raw == "SIM"

    snippet = {
        "title": titulo[:100],
        "description": descricao[:5000],
        "categoryId": "22",
    }

    status = {
        "privacyStatus": privacidade if privacidade in ("public", "unlisted", "private") else "public",
        "selfDeclaredMadeForKids": publico_infantil,
    }

    publish_at = build_publish_at(row)
    if publish_at:
        status["privacyStatus"] = "private"
        status["publishAt"] = publish_at

    return {"snippet": snippet, "status": status}


def check_required_columns(df: pd.DataFrame) -> list[str]:
    missing = []
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            missing.append(col)
    return missing


def validate_publication_rows(df: pd.DataFrame):
    mask = (
        df["Plataforma"].astype(str).str.upper().str.strip().eq("YT")
        & df["Publicar"].astype(str).str.upper().str.strip().eq("SIM")
        & ~df["StatusPublicacao"]
        .astype(str)
        .str.upper()
        .str.strip()
        .isin(["PUBLICADO", "AGENDADO"])
    )

    problems = []
    valid_privacies = {"public", "unlisted", "private"}
    valid_kids = {"SIM", "NAO"}

    for idx, row in df[mask].iterrows():
        excel_row = idx + 2
        issues = []

        titulo = str(row.get("TituloShort") or row.get("Titulo") or "").strip()
        if not titulo:
            issues.append("TituloShort/Titulo vazio")

        privacidade = str(row.get("Privacidade") or "").strip().lower()
        if privacidade and privacidade not in valid_privacies:
            issues.append(f"Privacidade inválida: '{privacidade}' (use public/unlisted/private)")

        publico_infantil_raw = str(row.get("PublicoInfantil") or "").strip().upper()
        if publico_infantil_raw == "NÃO":
            publico_infantil_raw = "NAO"

        if publico_infantil_raw and publico_infantil_raw not in valid_kids:
            issues.append(f"PublicoInfantil inválido: '{publico_infantil_raw}' (use SIM/NAO)")

        data_pub = row.get("DataPublicacao")
        hora_pub = row.get("HoraPublicacao")
        if pd.isna(data_pub) or pd.isna(hora_pub) or not str(data_pub).strip() or not str(hora_pub).strip():
            issues.append("DataPublicacao/HoraPublicacao vazias (obrigatório para agendamento)")

        if issues:
            problems.append((excel_row, issues))

    return problems


def publish_shorts() -> None:
    if not Path(EXCEL_PATH).exists():
        print(f"ERRO: Arquivo Excel não encontrado em {EXCEL_PATH}")
        sys.exit(1)

    try:
        sheets = pd.read_excel(EXCEL_PATH, sheet_name=None)
    except Exception as e:
        print(f"ERRO ao ler Excel: {e}")
        sys.exit(1)

    if "Shorts" not in sheets:
        print("ERRO: Aba 'Shorts' não encontrada na planilha.")
        sys.exit(1)

    df = sheets["Shorts"]
    missing_cols = check_required_columns(df)
    if missing_cols:
        cols = ", ".join(missing_cols)
        print("ERRO: Colunas obrigatórias de publicação ausentes na aba 'Shorts'.")
        print(f"Faltando: {cols}")
        print("Rode primeiro: python scripts/update_roteiro_shorts_columns.py")
        sys.exit(1)

    pub_problems = validate_publication_rows(df)
    if pub_problems:
        print("❌ Erros de configuração de publicação encontrados na aba 'Shorts':")
        for excel_row, issues in pub_problems:
            print(f"- Linha {excel_row}:")
            for msg in issues:
                print(f"    • {msg}")
        print("Ajuste a planilha e rode novamente o script de publicação.")
        sys.exit(1)

    LOGS_DIR.mkdir(exist_ok=True)

    class DualLogger:
        def __init__(self, filepath):
            self.terminal = sys.stdout
            self.log = open(filepath, "w", encoding="utf-8")

        def write(self, message):
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted = f"[{ts}] {message}"
            self.terminal.write(formatted)
            self.log.write(formatted)

        def flush(self):
            self.terminal.flush()
            self.log.flush()

    log_file = LOGS_DIR / "publicacao_shorts_ultimo_log.txt"
    sys.stdout = DualLogger(log_file)

    print("=== INÍCIO DA RODADA DE PUBLICAÇÃO DE SHORTS ===\n")

    # DEBUG: Diagnóstico de filtros
    total_rows = len(df)
    yt_count = df["Plataforma"].astype(str).str.upper().str.strip().eq("YT").sum()
    sim_count = df["Publicar"].astype(str).str.upper().str.strip().eq("SIM").sum()
    not_pub_count = df["StatusPublicacao"].astype(str).str.upper().str.strip().ne("PUBLICADO").sum()
    
    print(f"DEBUG DIAGNÓSTICO:")
    print(f"- Total de linhas: {total_rows}")
    print(f"- Plataforma='YT': {yt_count}")
    print(f"- Publicar='SIM': {sim_count}")
    print(f"- Status!='PUBLICADO': {not_pub_count}")

    mask = (
        df["Plataforma"].astype(str).str.upper().str.strip().eq("YT")
        & df["Publicar"].astype(str).str.upper().str.strip().eq("SIM")
        & df["StatusPublicacao"].astype(str).str.upper().str.strip().ne("PUBLICADO")
    )

    pending = df[mask]
    if pending.empty:
        print("Nenhum Short pendente para publicação no YouTube.")
        return

    print(f"Encontrados {len(pending)} Shorts pendentes para publicar.")

    tokens_disponiveis = sorted(
        {(str(row.get("CanalDestino", "")).strip().upper() or "DEFAULT") for _, row in pending.iterrows()}
    )

    if tokens_disponiveis:
        print("Canais detectados na coluna CanalDestino:")
        for idx, code in enumerate(tokens_disponiveis, start=1):
            rotulo = "DEFAULT" if code == "DEFAULT" else code
            print(f"{idx} - {rotulo}")
        print("0 - Todos os canais acima")

        if "--all" in sys.argv:
            print("Modo automático: publicando em todos os canais.")
            escolha = "0"
        else:
            escolha = input("Escolha o canal para publicar (número, Enter para todos): ").strip()

        canais_selecionados = set(tokens_disponiveis)
        if escolha:
            try:
                op = int(escolha)
                if op == 0:
                    canais_selecionados = set(tokens_disponiveis)
                elif 1 <= op <= len(tokens_disponiveis):
                    canais_selecionados = {tokens_disponiveis[op - 1]}
                else:
                    print("Opção inválida, publicando em todos os canais.")
            except ValueError:
                print("Entrada inválida, publicando em todos os canais.")
    else:
        canais_selecionados = {"DEFAULT"}

    services_cache = {}

    for idx, row in pending.iterrows():
        excel_row = idx + 2
        try:
            canal_destino = str(row.get("CanalDestino", "")).strip().upper()
            token_key = canal_destino or "DEFAULT"

            if token_key not in canais_selecionados:
                continue

            if token_key not in services_cache:
                print(f"Conectando ao YouTube para o canal '{token_key}'...")
                services_cache[token_key] = get_youtube_service(canal_destino)

            youtube = services_cache[token_key]

            video_path = build_video_path_short(row, Path(OUTPUT_SHORTS))
            if not video_path.exists():
                print(f"Linha {excel_row}: vídeo não encontrado em {video_path}")
                df.at[idx, "StatusPublicacao"] = "ERRO_VIDEO"
                continue

            metadata = build_metadata(row)
            media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True)

            print(f"Linha {excel_row}: enviando vídeo {video_path.name} para o YouTube...")

            request = youtube.videos().insert(
                part="snippet,status",
                body=metadata,
                media_body=media,
            )

            response = request.execute()
            video_id = response.get("id")
            if not video_id:
                print(f"Linha {excel_row}: retorno sem ID de vídeo, marcando como ERRO.")
                df.at[idx, "StatusPublicacao"] = "ERRO_API"
                continue

            url = f"https://www.youtube.com/shorts/{video_id}"
            df.at[idx, "YouTubeVideoId"] = video_id
            df.at[idx, "YouTubeURL"] = url

            status_final = "PUBLICADO"
            if metadata.get("status", {}).get("publishAt"):
                status_final = "AGENDADO"

            df.at[idx, "StatusPublicacao"] = status_final
            df.at[idx, "Publicar"] = "NAO"

            print(f"Linha {excel_row}: publicado com sucesso. URL: {url} (Status: {status_final})")

        except Exception as e:
            print(f"Linha {excel_row}: erro ao publicar Short: {e}")
            df.at[idx, "StatusPublicacao"] = "ERRO"

    sheets["Shorts"] = df

    try:
        with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="w") as writer:
            for name, sheet_df in sheets.items():
                sheet_df.to_excel(writer, sheet_name=name, index=False)
        print("Atualização da planilha após publicação concluída.")
    except PermissionError:
        print(f"ERRO: não foi possível salvar a planilha em {EXCEL_PATH}")
        print("Feche o arquivo Roteiro_Geral.xlsx no Excel e rode o script de publicação novamente.")

    print("\n=== FIM DA RODADA DE PUBLICAÇÃO DE SHORTS ===")


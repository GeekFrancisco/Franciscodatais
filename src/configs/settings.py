import os

# --- CAMINHOS BASE DO PROJETO ---
# Como este arquivo está em src/configs/settings.py, subimos 2 níveis para src e mais 1 para a raiz
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ASSETS_DIR = os.path.join(BASE_DIR, "assets")
TEMP_AUDIO_DIR = os.path.join(BASE_DIR, "temp_audios")

# Caminhos unificados (User request: Planilha única com abas Shorts/Longos)
EXCEL_PATH = os.path.join(BASE_DIR, "roteiros", "Roteiro_Geral.xlsx")

# --- CAMINHOS ESPECÍFICOS (SHORTS) ---
INPUT_IMAGES_SHORTS = os.path.join(BASE_DIR, "SHORTS", "input_images")
OUTPUT_SHORTS = os.path.join(BASE_DIR, "SHORTS", "output_videos_finais")

# --- CAMINHOS ESPECÍFICOS (LONGOS) ---
INPUT_IMAGES_LONGS = os.path.join(BASE_DIR, "LONGOS", "input_images")
OUTPUT_LONGS = os.path.join(BASE_DIR, "LONGOS", "output_videos")

# Mantido para compatibilidade se necessário, mas preferir os específicos acima
INPUT_IMAGES_DIR = INPUT_IMAGES_SHORTS 
OUTPUT_DIR = OUTPUT_SHORTS

def _find_font(candidates):
    windows_fonts_dir = r"C:\Windows\Fonts"
    for name in candidates:
        possible = []
        if os.path.isabs(name):
            possible.append(name)
        else:
            possible.append(name)
            possible.append(os.path.join(ASSETS_DIR, name))
            possible.append(os.path.join(windows_fonts_dir, name))
        for path in possible:
            if os.path.exists(path):
                return path
    return None

font_path_bold = _find_font([
    "Cinzel-Bold.ttf",
    "Lora-Bold.ttf",
    "PlayfairDisplay-Bold.ttf",
    "Montserrat-Bold.ttf",
    "Montserrat-SemiBold.ttf",
    "arialbd.ttf",
])
if not font_path_bold:
    font_path_bold = "arialbd.ttf"

font_path_semibold = _find_font([
    "Cinzel-Bold.ttf",
    "Lora-Bold.ttf",
    "PlayfairDisplay-Regular.ttf",
    "Cinzel-Regular.ttf",
    "Montserrat-SemiBold.ttf",
    "Montserrat-Medium.ttf",
    "Montserrat-Regular.ttf",
    "arialbd.ttf",
])

font_path_extra_bold = _find_font([
    "TheBoldFont.ttf",
    "Impact.ttf",
    "Montserrat-ExtraBold.ttf",
    "Montserrat-Bold.ttf",
    "arialbd.ttf",
])
if not font_path_semibold:
    font_path_semibold = font_path_bold

font_path_regular = _find_font([
    "Cinzel-Regular.ttf",
    "Lora-Regular.ttf",
    "PlayfairDisplay-Regular.ttf",
    "Montserrat-Regular.ttf",
    "arial.ttf"
])
if not font_path_regular:
    font_path_regular = "arial.ttf"

font_path = font_path_bold

COMMON_CONFIG = {
    "FPS": 30,
    "FONT_PATH": font_path,
    "FONT_PATH_BOLD": font_path_bold,
    "FONT_PATH_SEMIBOLD": font_path_semibold,
    
    # Configurações de Voz (Edge-TTS)
    "VOICE_EN": "en-US-ChristopherNeural",
    "VOICE_ES": "es-ES-AlvaroNeural",
    "VOICE_PT": "pt-BR-AntonioNeural",
    "VOICE_RATE": "-10%", # Velocidade da fala (mais natural)
}

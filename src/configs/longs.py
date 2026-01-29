from src.configs.settings import COMMON_CONFIG

# --- CONFIGURAÇÕES ESPECÍFICAS PARA LONGOS (HORIZONTAL) ---
LONGS_CONFIG = COMMON_CONFIG.copy()

LONGS_CONFIG.update({
    "WIDTH": 1920,
    "HEIGHT": 1080,
    
    # Efeito Ken Burns (Zoom/Pan) - Cinemático Lento
    "ZOOM_SPEED": 0.002, 
    "PAN_SPEED": 0, 
    "SLIDE_DURATION": 10, 
    
    # Tipografia e Layout (Fontes maiores para TV/Desktop)
    "FONT_SIZE_TITLE_MAIN": 110,
    "FONT_SIZE_TITLE_SECONDARY": 60,
    "FONT_SIZE_SUBTITLE": 85,
    "COLOR_TITLE": "#FFFFFF",
    "COLOR_TITLE_SECONDARY": "#00FFFF",
    "COLOR_SUBTITLE": "#FFD700",
    "COLOR_WATERMARK": "#FFFFFF",
    "FONT_SIZE_WATERMARK": 40,

    # Timings & Sync
    "PADDING_START": 2.0, 
    "PADDING_END": 3.0,
    "SUBTITLE_OFFSET": -0.20, # Ajuste de Sincronia (Segundos)
    "THUMB_INTRO_DURATION": 2.0, # Duração da Thumbnail Estática no início

    # Textos de Inscrição
    "SUBSCRIBE_TEXTS": {
        "EN": "SUBSCRIBE",
        "PT": "INSCREVA-SE",
        "ES": "SUSCRÍBETE"
    }
})

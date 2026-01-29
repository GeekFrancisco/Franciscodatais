from src.configs.settings import font_path_regular, font_path_bold, font_path_semibold, font_path_extra_bold

SHORTS_CONFIG = {
    # Resolução (9:16)
    "WIDTH": 1080,
    "HEIGHT": 1920,
    "FPS": 30,

    # Cores
    "COLOR_TITLE": "#FFFFFF",
    "COLOR_SUBTITLE": "#FFFF00", # Amarelo Puro (User Request)
    "COLOR_HIGHLIGHT": "#FFFF00", # Amarelo Puro
    "COLOR_WATERMARK": "white",
    
    # Fontes
    "FONT_PATH": font_path_regular,
    "FONT_PATH_BOLD": font_path_bold,
    "FONT_PATH_SEMIBOLD": font_path_semibold,
    "FONT_PATH_EXTRA_BOLD": font_path_extra_bold,
    "FONT_PATH_SUBSCRIBE": font_path_bold, # Usa Bold para CTA
    
    # Tamanhos (Ajustados para Word-by-Word Viral)
    "FONT_SIZE_TITLE_MAIN": 80,
    "FONT_SIZE_SUBTITLE": 130, # Bem grande para uma palavra
    "FONT_SIZE_SUBSCRIBE": 70, # Tamanho do CTA
    
    # Áudio
    "VOICE_RATE": "+0%", # Mais rápido para Shorts? Ou normal.
    "VOICE_EN": "en-US-ChristopherNeural", 
    "VOICE_PT": "pt-BR-AntonioNeural",
    "VOICE_ES": "es-ES-AlvaroNeural",
    
    # Timing
    "SUBTITLE_OFFSET": 0.00, # Ajuste fino de sincronia

    # Textos de CTA (Chamada para Ação)
    "SUBSCRIBE_TEXTS": {
        "EN": ["SUBSCRIBE", "FOLLOW FOR MORE", "JOIN US"],
        "PT": ["INSCREVA-SE", "SIGA PARA MAIS", "CURTA E COMPARTILHE"],
        "ES": ["SUSCRÍBETE", "SÍGUENOS", "COMPARTE", "ÚNETE"]
    }
}

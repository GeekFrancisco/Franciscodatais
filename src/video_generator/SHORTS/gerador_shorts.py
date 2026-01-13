import random
import asyncio
import os
import textwrap
import wave
import math
import struct
import pandas as pd
import edge_tts
from mutagen.mp3 import MP3
from moviepy import VideoClip, AudioFileClip, CompositeVideoClip, ImageClip, CompositeAudioClip, AudioClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# --- IMPORTAÇÃO ROBUSTA DO AUDIOARRAYCLIP ---
try:
    # Tenta importar da localização padrão (v1 e algumas v2)
    from moviepy.audio.AudioClip import AudioArrayClip
except ImportError:
    try:
        # Tenta importar do pacote principal
        from moviepy import AudioArrayClip
    except ImportError:
        try:
            # Tenta importar do editor (v1 antiga)
            from moviepy.editor import AudioArrayClip
        except ImportError:
            # FALLBACK: Se não existir, criamos uma classe compatível manualmente
            print("AVISO: AudioArrayClip não encontrado. Usando implementação fallback.")
            class AudioArrayClip(AudioClip):
                def __init__(self, array, fps):
                    self.array = array
                    self.fps = fps
                    duration = len(array) / fps
                    
                    def make_frame(t):
                        # t pode ser float ou array numpy
                        indices = (np.array(t) * fps).astype(int)
                        # Garante limites para não crashar
                        indices = np.clip(indices, 0, len(array) - 1)
                        return array[indices]
                        
                    super().__init__(make_frame=make_frame, duration=duration)


# --- CONFIGURAÇÕES ---
CONFIG = {
    "WIDTH": 1080,
    "HEIGHT": 1920,
    "FPS": 30,
    "ZOOM_SPEED": 0.04,
    "PAN_SPEED": 5,
    "FONT_SIZE_TITLE_MAIN": 80, # Levemente reduzido
    "FONT_SIZE_TITLE_SECONDARY": 45,
    "FONT_SIZE_SUBTITLE": 70,
    "COLOR_TITLE": "#FFFFFF", 
    "COLOR_TITLE_SECONDARY": "#00FFFF", # Ciano/Azul claro para diferenciar
    "COLOR_SUBTITLE": "#FFD700", # Amarelo Ouro (Chama mais atenção)
    "COLOR_WATERMARK": "#FFFFFF", # Branco para marca d'água
    "FONT_SIZE_WATERMARK": 30,
    "FONT_PATH": "arialbd.ttf",  # Arial Bold (Mais peso)
    
    # Configuração das Vozes
    "VOICE_EN": "en-US-ChristopherNeural",
    "VOICE_ES": "es-ES-AlvaroNeural",
    "VOICE_PT": "pt-BR-AntonioNeural",
    "VOICE_RATE": "-10%", # Mais lento para ser mais melódico/calmo
    
    # Timing Adjustments
    "PADDING_START": 3.0,
    "PADDING_END": 3.0
}

SUBSCRIBE_TEXTS = {
    "EN": "SUBSCRIBE",
    "PT": "INSCREVA-SE",
    "ES": "SUSCRÍBETE"
}

def generate_default_subscribe_sfx(filepath):
    """Gera um efeito sonoro de 'Sino' sintético (WAV) se não existir arquivo."""
    if os.path.exists(filepath): return
    
    print(f"🔊 Gerando SFX padrão (Sino) em: {filepath}")
    try:
        sample_rate = 44100
        duration = 1.5
        frequency = 1000.0 # 1kHz (Sino)

        num_samples = int(sample_rate * duration)
        
        # Gera WAV (mas salva com extensão do filepath, moviepy detecta header)
        with wave.open(filepath, 'w') as wav_file:
            wav_file.setnchannels(1) # Mono
            wav_file.setsampwidth(2) # 16 bit
            wav_file.setframerate(sample_rate)
            
            for i in range(num_samples):
                t = float(i) / sample_rate
                envelope = math.exp(-5 * t) # Decay rápido
                
                # Som de sino (Fundamental + Harmônicos)
                value = 0.5 * math.sin(2 * math.pi * frequency * t)
                value += 0.3 * math.sin(2 * math.pi * (frequency * 2) * t)
                
                sample = value * envelope * 32000.0
                if sample > 32767: sample = 32767
                if sample < -32768: sample = -32768
                
                wav_file.writeframes(struct.pack('h', int(sample)))
    except Exception as e:
        print(f"Erro ao gerar SFX: {e}")

# --- FUNÇÕES AUXILIARES DE TEXTO (PIL) ---
def create_text_image(text, width, font_size, color, bg_color=None, align='center', stroke_width=2, stroke_fill='black'):
    """Cria uma imagem PIL com o texto desenhado, para evitar dependência do ImageMagick."""
    try:
        font = ImageFont.truetype(CONFIG["FONT_PATH"], font_size)
    except IOError:
        font = ImageFont.load_default()
        print("AVISO: Fonte Arial não encontrada, usando padrão.")

    # Wrap do texto
    avg_char_width = font.getlength("x")
    max_chars = int((width - 100) / avg_char_width) # Margem de segurança
    lines = textwrap.wrap(text, width=max_chars)
    
    # Calcula altura necessária
    line_height = int(font.getbbox("hg")[3] * 1.5)
    img_height = line_height * len(lines) + 20
    
    # Cria imagem transparente
    img = Image.new('RGBA', (width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Desenha Fundo (Box) semi-transparente se solicitado
    if bg_color:
        # Calcula bounding box total do texto
        # Padding
        p = 10
        
        # Encontra largura máxima das linhas
        max_line_w = 0
        for line in lines:
            w = font.getlength(line)
            if w > max_line_w: max_line_w = w
            
        box_w = max_line_w + (p * 4)
        box_h = img_height - 10 # Ajuste fino
        
        box_x = (width - box_w) / 2
        box_y = 5
        
        draw.rounded_rectangle(
            [box_x, box_y, box_x + box_w, box_y + box_h], 
            radius=15, 
            fill=bg_color
        )

    y = 10
    for line in lines:
        # Centraliza cada linha
        line_w = font.getlength(line)
        x = (width - line_w) / 2
        
        # Borda (Stroke)
        for adj in range(-stroke_width, stroke_width+1):
             for adj2 in range(-stroke_width, stroke_width+1):
                 draw.text((x+adj, y+adj2), line, font=font, fill=stroke_fill)
                 
        draw.text((x, y), line, font=font, fill=color)
        y += line_height
        
    return np.array(img)

def estimate_word_timings(text, duration):
    """Fallback: Estima tempos das palavras matematicamente."""
    words = text.split()
    if not words: return []
    
    avg_duration = duration / len(words)
    timings = []
    current_time = 0
    
    for word in words:
        timings.append({
            "word": word,
            "start": current_time,
            "end": current_time + avg_duration
        })
        current_time += avg_duration
        
    return timings

async def generate_audio_and_word_timings(text, voice, audio_path):
    """Gera áudio e retorna tempos exatos de cada palavra para estilo Karaokê."""
    # Aplica ajuste de velocidade se definido
    rate = CONFIG.get("VOICE_RATE", "+0%")
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    word_timings = []
    
    # Remove arquivo anterior se existir para garantir nova gravação
    if os.path.exists(audio_path):
        os.remove(audio_path)

    with open(audio_path, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start_sec = chunk["audio_offset"] / 10_000_000
                duration_sec = chunk["duration"] / 10_000_000
                word_len = chunk["word_length"]
                text_offset = chunk["text_offset"]
                word = text[text_offset : text_offset + word_len]
                
                word_timings.append({
                    "word": word,
                    "start": start_sec,
                    "end": start_sec + duration_sec
                })
                
    return word_timings

def create_highlighted_text_image(text, width, font_size, color, highlight_word_index=None):
    """Cria imagem de texto com uma palavra em destaque (cor diferente)."""
    # Simplificação: Por enquanto, manteremos cor uniforme para garantir legibilidade rápida no vídeo
    # Para destaque real, precisaríamos desenhar palavra por palavra com cores diferentes
    return create_text_image(text, width, font_size, color, stroke_width=4)

def create_karaoke_clips(word_timings, video_duration, words_per_chunk=3):
    """Cria clips de legenda dinâmica (poucas palavras por vez)."""
    clips = []
    if not word_timings:
        return []

    # Agrupa palavras em blocos
    chunk = []
    
    # Lógica de agrupamento
    current_chunk = []
    
    for i, item in enumerate(word_timings):
        current_chunk.append(item)
        
        if len(current_chunk) >= words_per_chunk or i == len(word_timings) - 1:
            # Define tempo do bloco
            start_time = current_chunk[0]["start"]
            end_time = current_chunk[-1]["end"]
            
            # Garante tempo mínimo de leitura
            if end_time - start_time < 0.3: end_time = start_time + 0.3
            
            # Texto do bloco
            text_str = " ".join([w["word"] for w in current_chunk])
            
            # Gera imagem com Fundo Box (Preto 60%)
            txt_img = create_text_image(
                text_str, 
                CONFIG["WIDTH"], 
                CONFIG["FONT_SIZE_SUBTITLE"], 
                CONFIG["COLOR_SUBTITLE"], # Amarelo
                bg_color=(0, 0, 0, 160), # Fundo Preto Semi-Transparente
                stroke_width=0 # Sem stroke porque tem fundo
            )
            
            txt_clip = (ImageClip(txt_img)
                        .with_position(('center', 1500))
                        .with_start(start_time)
                        .with_duration(end_time - start_time))
            
            clips.append(txt_clip)
            current_chunk = []
            
    return clips

# --- FUNÇÕES DE VÍDEO (KEN BURNS) ---
def create_vignette_overlay(duration):
    """Cria uma sombra (degradê) preta na parte inferior e superior para destacar o texto."""
    w, h = CONFIG["WIDTH"], CONFIG["HEIGHT"]
    
    # Cria array RGBA
    # Gradiente vertical: Preto no topo (0-20%), Transparente no meio, Preto no fundo (80-100%)
    gradient = np.zeros((h, w, 4), dtype=np.uint8)
    
    # Definindo a opacidade (Alpha)
    # Topo: 0 a 150 (0.6 opacity) nos primeiros 15% pixels
    top_limit = int(h * 0.15)
    bottom_limit = int(h * 0.75)
    
    for y in range(h):
        alpha = 0
        if y < top_limit:
            # Topo escurecendo
            alpha = int(150 * (1 - y/top_limit))
        elif y > bottom_limit:
            # Fundo escurecendo
            alpha = int(180 * ((y - bottom_limit) / (h - bottom_limit)))
            
        if alpha > 0:
            gradient[y, :, 0] = 0 # R
            gradient[y, :, 1] = 0 # G
            gradient[y, :, 2] = 0 # B
            gradient[y, :, 3] = alpha # A
            
    img = Image.fromarray(gradient)
    return ImageClip(np.array(img)).with_duration(duration)

def apply_ken_burns_effect(image_path, duration, zoom_direction=1, pan_direction=1):
    """
    Gera o clipe com Zoom e Pan.
    zoom_direction: 1 (Zoom In) ou -1 (Zoom Out)
    pan_direction: 1 (Direita/Baixo) ou -1 (Esquerda/Cima)
    """
    original_img = Image.open(image_path).convert('RGB')
    
    # 1. Ajuste inicial (Cover)
    target_ratio = CONFIG["WIDTH"] / CONFIG["HEIGHT"]
    img_ratio = original_img.width / original_img.height
    
    if img_ratio > target_ratio:
        base_h = CONFIG["HEIGHT"]
        base_w = int(base_h * img_ratio)
    else:
        base_w = CONFIG["WIDTH"]
        base_h = int(base_w / img_ratio)
        
    # Redimensiona inicial com alta qualidade
    original_resized = original_img.resize((base_w, base_h), Image.LANCZOS)
    
    def make_frame(t):
        # Progresso (0 a 1)
        progress = t / duration
        
        # ZOOM
        # Se direction=1: Scale vai de 1.0 -> 1.0 + ZOOM_SPEED
        # Se direction=-1: Scale vai de 1.0 + ZOOM_SPEED -> 1.0
        max_scale = 1 + CONFIG["ZOOM_SPEED"] * duration # Zoom acumulado
        
        if zoom_direction == 1:
            scale = 1 + (max_scale - 1) * progress
        else:
            scale = max_scale - (max_scale - 1) * progress
            
        # Garante que scale nunca seja menor que 1
        if scale < 1.0: scale = 1.0
        
        current_w = int(base_w * scale)
        current_h = int(base_h * scale)
        
        # Resize do frame
        img = original_resized.resize((current_w, current_h), Image.LANCZOS)
        
        # PAN (Movimento)
        max_offset_x = current_w - CONFIG["WIDTH"]
        max_offset_y = current_h - CONFIG["HEIGHT"]
        
        # Posição central
        center_x = max_offset_x / 2
        center_y = max_offset_y / 2
        
        # Deslocamento
        pan_offset = CONFIG["PAN_SPEED"] * t * pan_direction
        
        pos_x = int(center_x + pan_offset)
        pos_y = int(center_y + pan_offset)
        
        # Clamp (Segurança absoluta)
        pos_x = max(0, min(pos_x, max_offset_x))
        pos_y = max(0, min(pos_y, max_offset_y))
        
        return np.array(img.crop((pos_x, pos_y, pos_x + CONFIG["WIDTH"], pos_y + CONFIG["HEIGHT"])))

    return VideoClip(make_frame, duration=duration)

# --- FUNÇÃO DE THUMBNAIL PRO (NUVEM BRANCA) ---
def create_pro_thumbnail(image_path, title, output_path, watermark=None):
    """Cria thumbnail com 'Nuvem' branca INFERIOR e Marca d'água SUPERIOR."""
    try:
        img = Image.open(image_path).convert("RGB")
        
        # 1. Crop/Resize para 1080x1920 (Centralizado)
        target_ratio = CONFIG["WIDTH"] / CONFIG["HEIGHT"]
        img_ratio = img.width / img.height
        
        if img_ratio > target_ratio:
            new_height = CONFIG["HEIGHT"]
            new_width = int(new_height * img_ratio)
            img = img.resize((new_width, new_height), Image.LANCZOS)
            left = (new_width - CONFIG["WIDTH"]) // 2
            img = img.crop((left, 0, left + CONFIG["WIDTH"], CONFIG["HEIGHT"]))
        else:
            new_width = CONFIG["WIDTH"]
            new_height = int(new_width / img_ratio)
            img = img.resize((new_width, new_height), Image.LANCZOS)
            top = (new_height - CONFIG["HEIGHT"]) // 2
            img = img.crop((0, top, CONFIG["WIDTH"], top + CONFIG["HEIGHT"]))
            
        draw = ImageDraw.Draw(img)
        
        # --- MARCA D'ÁGUA (TOPO) ---
        if watermark and watermark.lower() != 'nan':
            try:
                wm_font = ImageFont.truetype(CONFIG["FONT_PATH"], 70) # Fonte maior para o canal
            except:
                wm_font = ImageFont.load_default()
            
            wm_bbox = wm_font.getbbox(watermark)
            wm_w = wm_bbox[2] - wm_bbox[0]
            wm_x = (CONFIG["WIDTH"] - wm_w) // 2
            wm_y = 100 # Bem no topo
            
            # Stroke Preto para leitura
            for adj in range(-3, 4):
                for adj2 in range(-3, 4):
                    draw.text((wm_x+adj, wm_y+adj2), watermark, font=wm_font, fill="black")
            draw.text((wm_x, wm_y), watermark, font=wm_font, fill="white")

        # --- TÍTULO NA NUVEM (EMBAIXO) ---
        # 2. Fonte Menor para não cobrir o rosto
        font_size = 85 
        try:
            font = ImageFont.truetype(CONFIG["FONT_PATH"], font_size)
        except:
            font = ImageFont.load_default()
            
        # 3. Prepara Texto
        lines = textwrap.wrap(title, width=14) # Mais caracteres por linha
        
        # Calcula dimensões
        line_height = font.getbbox("Ay")[3] + 15
        text_h = line_height * len(lines)
        text_w = 0
        for line in lines:
            w = font.getlength(line)
            if w > text_w: text_w = w
            
        # 4. Desenha a 'Nuvem' (BEM EMBAIXO)
        padding = 50
        cloud_w = text_w + (padding * 2)
        cloud_h = text_h + (padding * 2)
        cloud_x = (CONFIG["WIDTH"] - cloud_w) // 2
        
        # Posição Y: 100px do fundo (Rodapé)
        cloud_y = CONFIG["HEIGHT"] - cloud_h - 100
        
        # Sombra da nuvem
        shadow_offset = 15
        draw.rounded_rectangle(
            [cloud_x + shadow_offset, cloud_y + shadow_offset, cloud_x + cloud_w + shadow_offset, cloud_y + cloud_h + shadow_offset],
            radius=60, fill="#333333"
        )
        
        # Nuvem Amarela (Mais chama atenção - Estilo Marca Texto)
        draw.rounded_rectangle(
            [cloud_x, cloud_y, cloud_x + cloud_w, cloud_y + cloud_h],
            radius=60, fill="#FFD700", outline="#FFD700", width=0
        )
        
        # 5. Desenha Texto (Preto Sólido - Sem Contorno para Leitura Rápida)
        curr_y = cloud_y + padding
        for line in lines:
            line_w = font.getlength(line)
            line_x = (CONFIG["WIDTH"] - line_w) // 2
            
            # Texto Preto
            draw.text((line_x, curr_y), line, font=font, fill="black")
            curr_y += line_height
            
        img.save(output_path, quality=100)
        return True
        
    except Exception as e:
        print(f"Erro ao criar thumbnail PRO: {e}")
        return False

# --- FUNÇÃO PRINCIPAL ---
async def processar_roteiro():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Caminho relativo para assets (onde está a música)
    assets_dir = os.path.join(os.path.dirname(base_dir), "assets")
    
    roteiro_path = os.path.join(base_dir, "Roteiros", "roteiro_versiculos.xlsx")
    img_dir = os.path.join(base_dir, "input_images")
    audio_dir = os.path.join(base_dir, "temp_audios")
    output_dir = os.path.join(base_dir, "output_videos_finais")
    
    # Garante que a pasta assets existe (só para log)
    if not os.path.exists(assets_dir):
        print(f"AVISO: Pasta assets não encontrada em {assets_dir}")
    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    # Verifica se o Excel existe
    if not os.path.exists(roteiro_path):
        print(f"ERRO: Crie o arquivo '{roteiro_path}' antes de rodar!")
        # Cria um Excel de exemplo para ajudar
        df_exemplo = pd.DataFrame({
            "Idioma": ["EN", "ES"],
            "Imagem": ["exemplo.jpg", "exemplo.jpg"],
            "Texto": ["The Lord is my shepherd.", "Jehová es mi pastor."],
            "Titulo": ["Psalm 23", "Salmo 23"]
        })
        df_exemplo.to_excel(roteiro_path, index=False)
        print(f"Criei um modelo em: {roteiro_path}. Preencha e rode de novo.")
        return

    # Lê o Excel
    df = pd.read_excel(roteiro_path)
    print(f"Encontrados {len(df)} vídeos para gerar.")

    for index, row in df.iterrows():
        print(f"\n--- Processando Vídeo {index + 1}/{len(df)} ---")
        
        idioma = row['Idioma'].strip().upper()
        texto = row['Texto']
        img_name = row['Imagem']
        titulo = str(row['Titulo'])
        
        # 1. Gerar Áudio (TTS) + Legendas Dinâmicas
        voice = CONFIG.get(f"VOICE_{idioma}", CONFIG["VOICE_EN"])
        audio_filename = f"audio_{index}.mp3"
        audio_path = os.path.join(audio_dir, audio_filename)
        
        print(f"Gerando áudio e sincronia ({idioma})...")
        word_timings = []
        
        # Tentativa de Retry (3x) para garantir WordBoundaries
        for attempt in range(3):
            try:
                word_timings = await generate_audio_and_word_timings(texto, voice, audio_path)
                if word_timings:
                    print(f"Palavras detectadas: {len(word_timings)}")
                    break # Sucesso
                else:
                    print(f"Tentativa {attempt+1}: Áudio gerado, mas sem tempos. Retentando...")
            except Exception as e:
                print(f"Tentativa {attempt+1} falhou com erro: {e}")
            
            await asyncio.sleep(5) # Espera 5s antes de tentar de novo (Reduz erro de conexão)
            
        # Fallback Final (Se depois de 3 tentativas não conseguir)
        if not word_timings:
            print("AVISO FINAL: Não foi possível obter tempos exatos. Usando estimativa matemática (Fallback).")
            
            # Verifica se o arquivo de áudio existe e é válido (> 1KB)
            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                try:
                    audio_len = MP3(audio_path).info.length
                    word_timings = estimate_word_timings(texto, audio_len)
                except Exception as e:
                    print(f"ERRO CRÍTICO: Arquivo de áudio corrompido ou inválido ({e}). Pulando vídeo.")
                    continue
            else:
                 print("ERRO CRÍTICO: Áudio não foi gerado ou está vazio. Pulando vídeo.")
                 continue # Pula este vídeo
        
        # Descobre duração do áudio
        try:
            audio_meta = MP3(audio_path)
            original_duration = audio_meta.info.length + 0.5
        except Exception as e:
             print(f"ERRO CRÍTICO ao ler duração do áudio: {e}. Pulando.")
             continue
        
        # Ajuste de Tempo: 3s silêncio inicial + áudio + 3s silêncio final
        duration = original_duration + CONFIG["PADDING_START"] + CONFIG["PADDING_END"]
        
        print(f"Duração Total: {duration:.2f}s (Áudio: {original_duration:.2f}s + Pausas)")
        
        # Ajusta Timings das palavras (Desloca 3s para frente)
        if word_timings:
            for w in word_timings:
                w["start"] += CONFIG["PADDING_START"]
                w["end"] += CONFIG["PADDING_START"]
        
        # 2. Gerar Vídeo Base (Ken Burns)
        img_path = os.path.join(img_dir, img_name)
        if not os.path.exists(img_path):
            print(f"ERRO: Imagem {img_name} não encontrada! Pulando...")
            continue
            
        print("Gerando vídeo base com animação (Ken Burns Aleatório)...")
        # Sorteia direção do Zoom e Pan para cada vídeo ficar único
        zoom_dir = random.choice([1, -1]) # 1=In, -1=Out
        pan_dir = random.choice([1, -1])  # 1=Right, -1=Left
        
        base_clip = apply_ken_burns_effect(img_path, duration, zoom_direction=zoom_dir, pan_direction=pan_dir)
        
        # Adiciona Vignette (Sombra) para melhorar leitura
        vignette_clip = create_vignette_overlay(duration)
        
        # 3. Gerar Clips de Texto
        print("Gerando legendas dinâmicas (estilo Shorts)...")
        
        # Título e Subtítulo
        # Prioridade: Coluna 'Subtitulo' > Split com '|' > Vazio
        titulo_raw = str(row['Titulo'])
        subtitulo_raw = str(row.get('Subtitulo', '')) 
        marca_dagua = str(row.get('MarcaDagua', '')) # Lê marca d'água
        
        if subtitulo_raw and subtitulo_raw.lower() != 'nan':
             main_title = titulo_raw.strip().upper()
             secondary_title = subtitulo_raw.strip().upper()
        else:
             # Fallback para lógica do separador pipe '|'
             titulo_parts = titulo_raw.split('|')
             main_title = titulo_parts[0].strip().upper()
             secondary_title = titulo_parts[1].strip().upper() if len(titulo_parts) > 1 else ""
        
        clips_to_add = []
        
        # 1. Título Principal (Hook) - Bem Grande
        title_y_pos = 150
        title_img = create_text_image(
            main_title, 
            CONFIG["WIDTH"], 
            CONFIG["FONT_SIZE_TITLE_MAIN"],
            CONFIG["COLOR_TITLE"], 
            stroke_width=6
        )
        # Animação de Entrada: Aparece em 0.5s para criar impacto
        title_clip = (ImageClip(title_img)
                      .with_position(('center', title_y_pos))
                      .with_start(0.5)
                      .with_duration(duration - 0.5))
        clips_to_add.append(title_clip)
        
        # 2. Título Secundário (Contexto) - Menor, logo abaixo (Posição Dinâmica)
        if secondary_title:
            sec_title_img = create_text_image(
                secondary_title, 
                CONFIG["WIDTH"], 
                CONFIG["FONT_SIZE_TITLE_SECONDARY"],
                CONFIG["COLOR_TITLE_SECONDARY"], 
                stroke_width=4
            )
            
            # Calcula posição baseada na altura do título principal para evitar sobreposição
            title_height = title_img.shape[0]
            sec_title_y_pos = title_y_pos + title_height - 10 # Ajuste fino para ficar próximo
            
            # Animação de Entrada: Aparece em 1.0s (depois do principal)
            sec_title_clip = (ImageClip(sec_title_img)
                          .with_position(('center', sec_title_y_pos)) 
                          .with_start(1.0)
                          .with_duration(duration - 1.0))
            clips_to_add.append(sec_title_clip)
        
        # 3. Marca D'água (Branding)
        if marca_dagua and marca_dagua.lower() != 'nan':
            watermark_img = create_text_image(
                marca_dagua, 
                CONFIG["WIDTH"], 
                CONFIG["FONT_SIZE_WATERMARK"], 
                CONFIG["COLOR_WATERMARK"], 
                stroke_width=2
            )
            # Posiciona no topo esquerdo ou rodapé discreto
            watermark_clip = (ImageClip(watermark_img)
                          .with_position(('center', 1750)) # Rodapé, abaixo da legenda
                          .with_opacity(0.7) # Semitransparente
                          .with_duration(duration))
            clips_to_add.append(watermark_clip)

        # 4. Call to Action (Universal - TikTok/Shorts/Reels)
        cta_text = SUBSCRIBE_TEXTS.get(idioma, "SUBSCRIBE")
        
        # Estilo Universal: Texto Branco Gigante com Borda Preta (Funciona em qualquer fundo)
        # Removemos o botão vermelho para não parecer exclusivo do YouTube
        cta_img = create_text_image(
            cta_text,
            CONFIG["WIDTH"],
            120, # Fonte Gigante para Impacto
            "white",
            stroke_width=8, # Borda grossa para leitura perfeita
            stroke_fill="black"
        )
        
        # Inicia um pouco antes do fim da fala para overlap suave (opcional), 
        # ou exato. Vamos fazer fade-in de 0.5s
        cta_start_time = duration - CONFIG["PADDING_END"]
        
        cta_clip = (ImageClip(cta_img)
                    .with_position('center')
                    .with_start(cta_start_time)
                    .with_duration(CONFIG["PADDING_END"]))
        
        # Tenta aplicar FadeIn (Compatibilidade v1/v2)
        try:
            # MoviePy v1
            cta_clip = cta_clip.crossfadein(0.5)
        except AttributeError:
            try:
                # MoviePy v2
                from moviepy.video.fx import FadeIn
                cta_clip = cta_clip.with_effects([FadeIn(0.5)])
            except ImportError:
                 print("AVISO: Efeito FadeIn não disponível.")

        clips_to_add.append(cta_clip)

        # Legendas Karaokê (3 palavras por vez)
        subtitle_clips = create_karaoke_clips(word_timings, duration, words_per_chunk=3)
        
        if not subtitle_clips:
            # Fallback se não detectar palavras
            print("AVISO: Falha na detecção de palavras. Usando texto completo.")
            full_text_img = create_text_image(texto, CONFIG["WIDTH"], CONFIG["FONT_SIZE_SUBTITLE"], CONFIG["COLOR_SUBTITLE"])
            subtitle_clips = [(ImageClip(full_text_img).with_position(('center', 1500)).with_duration(duration))]
        
        # 4. Composição Final (Base + Vignette + Textos)
        final_video = CompositeVideoClip([base_clip, vignette_clip] + clips_to_add + subtitle_clips)
        
        # 5. Adicionar Áudio (Narração + Música de Fundo)
        # Narração começa após o PADDING_START (3s)
        speech_audio = AudioFileClip(audio_path).with_start(CONFIG["PADDING_START"])
        
        # Tenta carregar a música de fundo da pasta assets
        bg_music_path = os.path.join(assets_dir, "Pulsar - The Grey Room _ Density & Time.mp3")
        
        # Lista de clipes de áudio para mixar
        audio_clips = [speech_audio]

        # --- MÚSICA DE FUNDO ---
        if os.path.exists(bg_music_path):
            try:
                bg_music = AudioFileClip(bg_music_path)
                
                # --- LÓGICA DE VOLUME VIA ARRAY (NUCLEAR OPTION) ---
                print("Processando áudio de fundo (Modo Robusto)...")
                
                if hasattr(bg_music, "subclipped"): # MoviePy v2
                    bg_music = bg_music.subclipped(0, duration)
                else: # MoviePy v1
                    bg_music = bg_music.subclip(0, duration)
                
                # 2. Converte para Array e manipula volume dinamicamente (Audio Ducking)
                arr = bg_music.to_soundarray()
                
                # Cria array de volume base (10%)
                volume_curve = np.ones(len(arr)) * 0.10 
                
                # Intro (0 a 3s): Volume mais alto (30%) para impacto inicial
                fps = bg_music.fps
                intro_end_frame = int(CONFIG["PADDING_START"] * fps)
                
                # Fade suave de 30% para 10% logo antes da fala começar
                if len(volume_curve) > intro_end_frame:
                    volume_curve[:intro_end_frame] = 0.30
                    
                    # Smooth transition (Fade Out da intro) - 0.5s de transição
                    transition_frames = int(0.5 * fps)
                    start_trans = intro_end_frame
                    end_trans = min(start_trans + transition_frames, len(volume_curve))
                    
                    # Interpolação linear de 0.30 para 0.10
                    if end_trans > start_trans:
                        volume_curve[start_trans:end_trans] = np.linspace(0.30, 0.10, end_trans - start_trans)

                # Aplica a curva de volume (Broadcast nas colunas estéreo)
                arr = arr * volume_curve[:, np.newaxis]
                
                bg_music = AudioArrayClip(arr, fps=bg_music.fps)
                
                audio_clips.append(bg_music)
                print(f"🎵 Música de fundo adicionada (Intro 30% -> Fala 10%): {os.path.basename(bg_music_path)}")
                
            except Exception as e:
                print(f"⚠️ ERRO FINAL AO PROCESSAR MÚSICA: {e}")
        else:
             print(f"⚠️ Música de fundo não encontrada em: {bg_music_path}")

        # --- EFEITO SONORO SUBSCRIBE ---
        subscribe_sfx_path = os.path.join(assets_dir, "subscribe.mp3")
        
        # Auto-gera se não existir
        generate_default_subscribe_sfx(subscribe_sfx_path)
        
        if os.path.exists(subscribe_sfx_path):
            try:
                # Começa junto com o texto de Subscribe (Duration - Padding End)
                start_time = duration - CONFIG["PADDING_END"]
                if start_time < 0: start_time = 0
                
                sub_sfx = AudioFileClip(subscribe_sfx_path).with_start(start_time)
                audio_clips.append(sub_sfx)
                print("🔔 SFX de Subscribe adicionado à mixagem.")
            except Exception as e:
                print(f"Erro ao adicionar SFX Subscribe: {e}")

        # Mixagem Final
        final_audio = CompositeAudioClip(audio_clips)

        final_output = final_video.with_audio(final_audio)
        
        # 6. Salvar Vídeo (Com Retry Logic para evitar BrokenPipeError)
        # Sanitiza nome do arquivo (Remove caracteres proibidos no Windows: < > : " / \ | ? *)
        import re
        safe_title = re.sub(r'[<>:"/\\|?*]', '', titulo).strip()
        
        # Extrai nome da imagem (sem extensão) para organização
        safe_img_name = os.path.splitext(img_name)[0].strip()
        
        output_filename = f"{idioma}_{safe_img_name}_{safe_title}_{index}.mp4".replace(" ", "_")
        output_path = os.path.join(output_dir, output_filename)
        
        success = False
        for attempt in range(1, 4):
            try:
                # Na primeira tentativa usa 4 threads, nas seguintes usa 1 (mais seguro)
                current_threads = 4 if attempt == 1 else 1
                print(f"🎬 Exportando vídeo (Tentativa {attempt}/3 - Threads: {current_threads})...")
                
                final_output.with_fps(CONFIG["FPS"]).write_videofile(
                    output_path, 
                    codec='libx264', 
                    audio_codec='aac', 
                    preset='ultrafast',
                    threads=current_threads,
                    logger=None
                )
                print(f"✅ Vídeo salvo com sucesso: {output_path}")
                success = True
                break
            except Exception as e:
                print(f"❌ Erro na exportação (Tentativa {attempt}): {e}")
                import time
                time.sleep(2) # Espera um pouco antes de tentar de novo
        
        if not success:
            print(f"☠️ FALHA CRÍTICA: Não foi possível salvar o vídeo {index}. Pulando.")
            continue

        # 7. Salvar Thumbnail PRO (Estilo Nuvem)
        thumb_filename = f"{idioma}_{safe_img_name}_{safe_title}_{index}_thumb.jpg".replace(" ", "_")
        thumb_path = os.path.join(output_dir, thumb_filename)
        
        print("🖼️ Gerando Thumbnail PRO (Nuvem Branca)...")
        # Usa a imagem original para criar uma capa limpa e chamativa
        thumb_success = create_pro_thumbnail(img_path, main_title, thumb_path, watermark=marca_dagua)
        
        if thumb_success:
            print(f"✅ Thumbnail salva: {thumb_filename}")
        else:
            # Fallback para captura de frame se der erro
            try:
                frame = final_output.get_frame(4.5)
                img_thumb = Image.fromarray(frame).convert("RGB")
                img_thumb.save(thumb_path, quality=95)
                print(f"🖼️ Thumbnail (Fallback) salva: {thumb_filename}")
                thumb_success = True
            except Exception as e:
                print(f"Erro ao salvar thumbnail fallback: {e}")
                thumb_success = False

        # --- EMBUTIR THUMBNAIL NO VÍDEO (METADATA) ---
        if thumb_success and os.path.exists(output_path) and os.path.exists(thumb_path):
            try:
                print("📎 Anexando Thumbnail ao arquivo de vídeo (Cover Art)...")
                temp_output = output_path.replace(".mp4", "_temp.mp4")
                
                # Comando FFmpeg para adicionar stream de imagem como cover
                # -map 0 (vídeo/audio original) -map 1 (imagem) -c copy (sem reencode)
                # -disposition:v:1 attached_pic (define como capa)
                cmd = [
                    "ffmpeg", "-y", "-i", output_path, "-i", thumb_path,
                    "-map", "0", "-map", "1",
                    "-c", "copy", "-disposition:v:1", "attached_pic",
                    temp_output
                ]
                
                # Executa silenciosamente
                import subprocess
                result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                if result.returncode == 0:
                    # Substitui o original pelo novo
                    os.replace(temp_output, output_path)
                    print("✅ Thumbnail embutida no MP4 com sucesso!")
                else:
                    print("⚠️ Falha ao embutir thumbnail (FFmpeg retornou erro). Mantendo vídeo original.")
                    if os.path.exists(temp_output): os.remove(temp_output)
                    
            except Exception as e:
                print(f"Erro ao executar FFmpeg para thumbnail: {e}")
            
        # 8. Limpeza de Arquivos Temporários e Liberação de Memória
        try:
            # Fecha clips para liberar recursos do FFmpeg
            final_video.close()
            final_audio.close()
            speech_audio.close()
            if 'bg_music' in locals(): bg_music.close()
            if 'sfx_audio' in locals(): sfx_audio.close()
        except:
            pass

        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                print("🧹 Áudio temporário removido.")
            except:
                pass

    print("\n--- Processamento Completo! ---")

if __name__ == "__main__":
    asyncio.run(processar_roteiro())
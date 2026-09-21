import random
import asyncio
import os
import textwrap
import pandas as pd
import edge_tts
from mutagen.mp3 import MP3
from moviepy import VideoClip, AudioFileClip, CompositeVideoClip, ImageClip, CompositeAudioClip, AudioClip, concatenate_videoclips, concatenate_audioclips
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# --- IMPORTAÇÃO ROBUSTA DO AUDIOARRAYCLIP ---
try:
    from moviepy.audio.AudioClip import AudioArrayClip
except ImportError:
    try:
        from moviepy import AudioArrayClip
    except ImportError:
        try:
            from moviepy.editor import AudioArrayClip
        except ImportError:
            class AudioArrayClip(AudioClip):
                def __init__(self, array, fps):
                    self.array = array
                    self.fps = fps
                    duration = len(array) / fps
                    def make_frame(t):
                        indices = (np.array(t) * fps).astype(int)
                        indices = np.clip(indices, 0, len(array) - 1)
                        return array[indices]
                    super().__init__(make_frame=make_frame, duration=duration)

# --- CONFIGURAÇÕES PARA VÍDEOS LONGOS (LANDSCAPE) ---
CONFIG = {
    "WIDTH": 1920,   # FULL HD Horizontal
    "HEIGHT": 1080,
    "FPS": 30,
    "ZOOM_SPEED": 0.04,
    "PAN_SPEED": 2,  # Mais lento para ser relaxante
    "SLIDE_DURATION": 10, # Troca de imagem a cada 10 segundos
    
    # Tipografia Otimizada para TV/Desktop
    "FONT_SIZE_TITLE_MAIN": 110,
    "FONT_SIZE_TITLE_SECONDARY": 60,
    "FONT_SIZE_SUBTITLE": 85,
    "COLOR_TITLE": "#FFFFFF", 
    "COLOR_TITLE_SECONDARY": "#00FFFF",
    "COLOR_SUBTITLE": "#FFD700",
    "COLOR_WATERMARK": "#FFFFFF",
    "FONT_SIZE_WATERMARK": 40,
    "FONT_PATH": "arialbd.ttf",
    
    # Vozes
    "VOICE_EN": "en-US-ChristopherNeural",
    "VOICE_ES": "es-ES-AlvaroNeural",
    "VOICE_PT": "pt-BR-AntonioNeural"
}

# --- FUNÇÕES DE TEXTO (IGUAL AO SHORTS, AJUSTADO PARA LARGURA) ---
def create_text_image(text, width, font_size, color, bg_color=None, align='center', stroke_width=2, stroke_fill='black'):
    try:
        font = ImageFont.truetype(CONFIG["FONT_PATH"], font_size)
    except IOError:
        font = ImageFont.load_default()

    avg_char_width = font.getlength("x")
    max_chars = int((width - 150) / avg_char_width) # Margem maior
    lines = textwrap.wrap(text, width=max_chars)
    
    line_height = int(font.getbbox("hg")[3] * 1.5)
    img_height = line_height * len(lines) + 20
    
    img = Image.new('RGBA', (width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    y = 10
    for line in lines:
        line_w = font.getlength(line)
        x = (width - line_w) / 2
        for adj in range(-stroke_width, stroke_width+1):
             for adj2 in range(-stroke_width, stroke_width+1):
                 draw.text((x+adj, y+adj2), line, font=font, fill=stroke_fill)
        draw.text((x, y), line, font=font, fill=color)
        y += line_height
        
    return np.array(img)

# --- ÁUDIO E SINCRONIA ---
def estimate_word_timings(text, duration):
    words = text.split()
    if not words: return []
    avg_duration = duration / len(words)
    timings = []
    current_time = 0
    for word in words:
        timings.append({"word": word, "start": current_time, "end": current_time + avg_duration})
        current_time += avg_duration
    return timings

async def generate_audio_and_word_timings(text, voice, audio_path):
    communicate = edge_tts.Communicate(text, voice)
    word_timings = []
    if os.path.exists(audio_path): os.remove(audio_path)
    
    with open(audio_path, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["audio_offset"] / 10_000_000
                dur = chunk["duration"] / 10_000_000
                word = text[chunk["text_offset"] : chunk["text_offset"] + chunk["word_length"]]
                word_timings.append({"word": word, "start": start, "end": start + dur})
    return word_timings

def create_karaoke_clips(word_timings, video_duration, words_per_chunk=6): # 6 palavras por vez (Horizontal)
    clips = []
    if not word_timings: return []
    
    current_chunk = []
    for i, item in enumerate(word_timings):
        current_chunk.append(item)
        if len(current_chunk) >= words_per_chunk or i == len(word_timings) - 1:
            start_time = current_chunk[0]["start"]
            end_time = current_chunk[-1]["end"]
            if end_time - start_time < 0.5: end_time = start_time + 0.5 # Tempo mínimo maior
            
            text_str = " ".join([w["word"] for w in current_chunk])
            txt_img = create_text_image(text_str, CONFIG["WIDTH"], CONFIG["FONT_SIZE_SUBTITLE"], CONFIG["COLOR_SUBTITLE"], stroke_width=5)
            
            # Posição: Inferior centralizado (Y=850 de 1080)
            txt_clip = (ImageClip(txt_img)
                        .with_position(('center', 850))
                        .with_start(start_time)
                        .with_duration(end_time - start_time))
            clips.append(txt_clip)
            current_chunk = []
    return clips

# --- VÍDEO E SLIDESHOW ---
def create_vignette_overlay(duration):
    w, h = CONFIG["WIDTH"], CONFIG["HEIGHT"]
    gradient = np.zeros((h, w, 4), dtype=np.uint8)
    # Sombra apenas na parte inferior para legendas
    bottom_limit = int(h * 0.65)
    for y in range(bottom_limit, h):
        alpha = int(200 * ((y - bottom_limit) / (h - bottom_limit)))
        gradient[y, :, 3] = alpha
    img = Image.fromarray(gradient)
    return ImageClip(np.array(img)).with_duration(duration)

def apply_ken_burns_single(image_path, duration):
    """Aplica Ken Burns em uma única imagem."""
    try:
        original_img = Image.open(image_path).convert('RGB')
    except Exception:
        return None

    # Lógica de Crop/Resize para 1920x1080
    target_ratio = CONFIG["WIDTH"] / CONFIG["HEIGHT"]
    img_ratio = original_img.width / original_img.height
    
    if img_ratio > target_ratio:
        base_h = CONFIG["HEIGHT"]
        base_w = int(base_h * img_ratio)
    else:
        base_w = CONFIG["WIDTH"]
        base_h = int(base_w / img_ratio)
        
    original_resized = original_img.resize((base_w, base_h), Image.LANCZOS)
    
    zoom_dir = random.choice([1, -1])
    pan_dir = random.choice([1, -1])
    
    def make_frame(t):
        progress = t / duration
        max_scale = 1 + CONFIG["ZOOM_SPEED"] * duration
        
        scale = 1 + (max_scale - 1) * progress if zoom_dir == 1 else max_scale - (max_scale - 1) * progress
        if scale < 1.0: scale = 1.0
        
        current_w, current_h = int(base_w * scale), int(base_h * scale)
        img = original_resized.resize((current_w, current_h), Image.LANCZOS)
        
        max_offset_x = current_w - CONFIG["WIDTH"]
        max_offset_y = current_h - CONFIG["HEIGHT"]
        
        center_x, center_y = max_offset_x / 2, max_offset_y / 2
        pan_offset = CONFIG["PAN_SPEED"] * t * pan_dir
        
        pos_x = int(max(0, min(center_x + pan_offset, max_offset_x)))
        pos_y = int(max(0, min(center_y + pan_offset, max_offset_y)))
        
        return np.array(img.crop((pos_x, pos_y, pos_x + CONFIG["WIDTH"], pos_y + CONFIG["HEIGHT"])))

    return VideoClip(make_frame, duration=duration)

def create_slideshow_clip(img_dir, total_duration):
    """Cria um slideshow infinito repetindo imagens da pasta."""
    valid_images = [os.path.join(img_dir, f) for f in os.listdir(img_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    
    if not valid_images:
        print("❌ ERRO: Nenhuma imagem encontrada para o slideshow!")
        # Cria imagem preta de fallback
        return VideoClip(lambda t: np.zeros((CONFIG["HEIGHT"], CONFIG["WIDTH"], 3), dtype=np.uint8), duration=total_duration)

    clips = []
    current_duration = 0
    img_idx = 0
    
    while current_duration < total_duration:
        remaining = total_duration - current_duration
        clip_dur = min(CONFIG["SLIDE_DURATION"], remaining)
        
        # Pega imagem (loop circular)
        img_path = valid_images[img_idx % len(valid_images)]
        clip = apply_ken_burns_single(img_path, clip_dur)
        
        if clip:
            clips.append(clip)
            current_duration += clip_dur
            img_idx += 1
        else:
            img_idx += 1 # Pula imagem corrompida
            
    # Concatena todos os clipes
    return concatenate_videoclips(clips, method="compose")

# --- PROCESSAMENTO PRINCIPAL ---
async def processar_roteiro_longo():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(os.path.dirname(base_dir), "assets")
    
    # Pastas Locais (Tudo dentro de LONGOS)
    roteiro_path = os.path.join(base_dir, "Roteiros", "roteiro_longos.xlsx")
    img_dir = os.path.join(base_dir, "input_images") 
    audio_dir = os.path.join(base_dir, "temp_audios")
    output_dir = os.path.join(base_dir, "output_videos")
    
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.dirname(roteiro_path), exist_ok=True)
    
    # 1. CRIA EXCEL SE NÃO EXISTIR
    if not os.path.exists(roteiro_path):
        print(f"⚠️ Roteiro não encontrado. Criando modelo em: {roteiro_path}")
        df_exemplo = pd.DataFrame({
            "Idioma": ["PT", "EN"],
            "Texto": [
                "Esta é uma oração longa de teste. Ela deve durar tempo suficiente para vermos a troca de imagens. O Senhor é meu pastor e nada me faltará. Ele me faz repousar em verdes pastos.", 
                "This is a long test prayer. It should last long enough for us to see the image swap. The Lord is my shepherd, I shall not want."
            ],
            "Titulo": ["ORAÇÃO DA MANHÃ", "MORNING PRAYER"],
            "Subtitulo": ["Salmo 23 Completo", "Psalm 23 Full"],
            "MarcaDagua": ["@CanalDeOração", "@PrayerChannel"]
        })
        df_exemplo.to_excel(roteiro_path, index=False)
        print("✅ Arquivo Excel criado! Preencha e rode novamente.")
        return

    df = pd.read_excel(roteiro_path)
    print(f"🎬 Iniciando processamento de {len(df)} vídeos longos.")

    for index, row in df.iterrows():
        print(f"\n--- Processando Vídeo Longo {index + 1}/{len(df)} ---")
        
        idioma = row['Idioma'].strip().upper()
        texto = row['Texto']
        titulo = str(row['Titulo'])
        subtitulo = str(row.get('Subtitulo', ''))
        
        # 1. Gera Áudio TTS
        voice = CONFIG.get(f"VOICE_{idioma}", CONFIG["VOICE_EN"])
        audio_filename = f"long_audio_{index}.mp3"
        audio_path = os.path.join(audio_dir, audio_filename)
        
        print("🎤 Gerando narração...")
        word_timings = []
        try:
            word_timings = await generate_audio_and_word_timings(texto, voice, audio_path)
        except Exception as e:
            print(f"Erro no TTS: {e}")
            continue
            
        if not word_timings and os.path.exists(audio_path):
             word_timings = estimate_word_timings(texto, MP3(audio_path).info.length)

        duration = MP3(audio_path).info.length + 2.0 # +2s de margem
        print(f"⏱️ Duração Total: {duration:.2f}s")
        
        # 2. Gera Slideshow (Base Visual)
        print("🖼️ Montando Slideshow (Ken Burns)...")
        # Usa apenas a pasta local de imagens
        source_img_dir = img_dir
        
        base_clip = create_slideshow_clip(source_img_dir, duration)
        vignette_clip = create_vignette_overlay(duration)
        
        # 3. Textos e Legendas
        print("📝 Gerando textos e legendas...")
        clips_to_add = []
        
        # Título Principal (Topo)
        title_img = create_text_image(titulo.upper(), CONFIG["WIDTH"], CONFIG["FONT_SIZE_TITLE_MAIN"], CONFIG["COLOR_TITLE"], stroke_width=6)
        title_clip = ImageClip(title_img).with_position(('center', 100)).with_duration(duration)
        clips_to_add.append(title_clip)
        
        # Subtítulo (Abaixo do título)
        if subtitulo:
            sub_img = create_text_image(subtitulo.upper(), CONFIG["WIDTH"], CONFIG["FONT_SIZE_TITLE_SECONDARY"], CONFIG["COLOR_TITLE_SECONDARY"], stroke_width=4)
            sub_clip = ImageClip(sub_img).with_position(('center', 250)).with_duration(duration)
            clips_to_add.append(sub_clip)
            
        # Legendas
        sub_clips = create_karaoke_clips(word_timings, duration, words_per_chunk=6)
        
        # 4. Composição
        final_video = CompositeVideoClip([base_clip, vignette_clip] + clips_to_add + sub_clips)
        
        # 5. Áudio Final (Com Loop de Música)
        speech_audio = AudioFileClip(audio_path)
        bg_music_path = os.path.join(assets_dir, "Pulsar - The Grey Room _ Density & Time.mp3")
        
        final_audio = speech_audio
        if os.path.exists(bg_music_path):
            try:
                bg_music = AudioFileClip(bg_music_path)
                # Loop manual da música para cobrir todo o vídeo
                num_loops = int(duration / bg_music.duration) + 2
                bg_music_looped = concatenate_audioclips([bg_music] * num_loops).subclipped(0, duration)
                
                # Volume via Array (Nuclear Option)
                arr = bg_music_looped.to_soundarray() * 0.16
                bg_music_final = AudioArrayClip(arr, fps=bg_music.fps)
                
                final_audio = CompositeAudioClip([speech_audio, bg_music_final])
                print("🎵 Música em loop aplicada.")
            except Exception as e:
                print(f"⚠️ Erro na música: {e}")
        
        final_output = final_video.with_audio(final_audio)
        
        # 6. Exportação
        safe_title = titulo.replace("|", "").replace("/", "").strip()
        output_filename = f"LONG_{idioma}_{safe_title}_{index}.mp4".replace(" ", "_")
        output_path = os.path.join(output_dir, output_filename)
        
        final_output.with_fps(CONFIG["FPS"]).write_videofile(
            output_path, codec='libx264', audio_codec='aac', preset='ultrafast', threads=4, logger=None
        )
        print(f"✅ Vídeo Longo Salvo: {output_path}")

    print("\n--- Processamento de Longos Completo! ---")

if __name__ == "__main__":
    asyncio.run(processar_roteiro_longo())
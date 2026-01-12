import asyncio
import os
import textwrap
import pandas as pd
import edge_tts
from mutagen.mp3 import MP3
from moviepy import VideoClip, AudioFileClip, CompositeVideoClip, ImageClip, CompositeAudioClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np

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
    "VOICE_PT": "pt-BR-AntonioNeural"
}

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
    communicate = edge_tts.Communicate(text, voice)
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
            
            # Gera imagem
            txt_img = create_text_image(
                text_str, 
                CONFIG["WIDTH"], 
                CONFIG["FONT_SIZE_SUBTITLE"], 
                CONFIG["COLOR_SUBTITLE"], # Amarelo
                stroke_width=6 # Stroke mais grosso para leitura em celular
            )
            
            txt_clip = (ImageClip(txt_img)
                        .with_position(('center', 1500))
                        .with_start(start_time)
                        .with_duration(end_time - start_time))
            
            clips.append(txt_clip)
            current_chunk = []
            
    return clips

# --- FUNÇÕES DE VÍDEO (KEN BURNS) ---
def apply_ken_burns_effect(image_path, duration):
    """Gera o clipe de vídeo com Zoom e Pan baseado na duração do áudio."""
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
        # Zoom progressivo
        scale = 1 + (CONFIG["ZOOM_SPEED"] * t)
        
        current_w = int(base_w * scale)
        current_h = int(base_h * scale)
        
        # Resize do frame (LANCZOS para evitar tremores)
        img = original_resized.resize((current_w, current_h), Image.LANCZOS)
        
        # Pan suave
        max_offset_x = current_w - CONFIG["WIDTH"]
        max_offset_y = current_h - CONFIG["HEIGHT"]
        
        center_x = max_offset_x / 2
        center_y = max_offset_y / 2
        
        # Deslocamento linear
        pan_offset = CONFIG["PAN_SPEED"] * t
        
        pos_x = int(round(center_x + pan_offset))
        pos_y = int(round(center_y + pan_offset))
        
        # Clamp (Segurança)
        if pos_x < 0: pos_x = 0
        if pos_x > max_offset_x: pos_x = max_offset_x
        if pos_y < 0: pos_y = 0
        if pos_y > max_offset_y: pos_y = max_offset_y
        
        return np.array(img.crop((pos_x, pos_y, pos_x + CONFIG["WIDTH"], pos_y + CONFIG["HEIGHT"])))

    return VideoClip(make_frame, duration=duration)

# --- FUNÇÃO PRINCIPAL ---
async def processar_roteiro():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    roteiro_path = os.path.join(base_dir, "roteiros", "roteiro_versiculos.xlsx")
    img_dir = os.path.join(base_dir, "input_images")
    audio_dir = os.path.join(base_dir, "temp_audios")
    output_dir = os.path.join(base_dir, "output_videos_finais")
    
    # Cria pastas necessárias
    os.makedirs(os.path.dirname(roteiro_path), exist_ok=True)
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
            
            await asyncio.sleep(2) # Espera antes de tentar de novo
            
        # Fallback Final (Se depois de 3 tentativas não conseguir)
        if not word_timings:
            print("AVISO FINAL: Não foi possível obter tempos exatos. Usando estimativa matemática (Fallback).")
            if os.path.exists(audio_path):
                 audio_len = MP3(audio_path).info.length
                 word_timings = estimate_word_timings(texto, audio_len)
            else:
                 print("ERRO CRÍTICO: Áudio nem sequer foi gerado.")
                 continue # Pula este vídeo
        
        # Descobre duração do áudio
        audio_meta = MP3(audio_path)
        duration = audio_meta.info.length + 0.5
        print(f"Duração do áudio: {duration:.2f}s")
        
        # 2. Gerar Vídeo Base (Ken Burns)
        img_path = os.path.join(img_dir, img_name)
        if not os.path.exists(img_path):
            print(f"ERRO: Imagem {img_name} não encontrada! Pulando...")
            continue
            
        print("Gerando vídeo base com animação...")
        base_clip = apply_ken_burns_effect(img_path, duration)
        
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
        title_clip = (ImageClip(title_img)
                      .with_position(('center', title_y_pos))
                      .with_duration(duration))
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
            
            sec_title_clip = (ImageClip(sec_title_img)
                          .with_position(('center', sec_title_y_pos)) 
                          .with_duration(duration))
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

        # Legendas Karaokê (3 palavras por vez)
        subtitle_clips = create_karaoke_clips(word_timings, duration, words_per_chunk=3)
        
        if not subtitle_clips:
            # Fallback se não detectar palavras
            print("AVISO: Falha na detecção de palavras. Usando texto completo.")
            full_text_img = create_text_image(texto, CONFIG["WIDTH"], CONFIG["FONT_SIZE_SUBTITLE"], CONFIG["COLOR_SUBTITLE"])
            subtitle_clips = [(ImageClip(full_text_img).with_position(('center', 1500)).with_duration(duration))]
        
        # 4. Composição Final
        final_video = CompositeVideoClip([base_clip] + clips_to_add + subtitle_clips)
        
        # 5. Adicionar Áudio (Narração + Música de Fundo)
        speech_audio = AudioFileClip(audio_path)
        
        # Tenta carregar a música de fundo específica
        bg_music_path = os.path.join(base_dir, "Pulsar - The Grey Room _ Density & Time.mp3")
        final_audio = speech_audio

        if os.path.exists(bg_music_path):
            try:
                bg_music = AudioFileClip(bg_music_path)
                
                # Ajusta volume (10%) - Lógica compatível com MoviePy v1 e v2
                if hasattr(bg_music, "multiply_volume"):
                    # MoviePy v2
                    bg_music = bg_music.multiply_volume(0.1)
                elif hasattr(bg_music, "volumex"):
                    # MoviePy v1
                    bg_music = bg_music.volumex(0.1)
                else:
                    # Tenta importar efeito v1
                    from moviepy.audio.fx.all import volumex
                    bg_music = bg_music.fx(volumex, 0.1)
                
                # Se a música for menor que o vídeo, faz loop (opcional, mas seguro)
                if bg_music.duration < duration:
                    pass 
                
                # Corta a música para ter o mesmo tamanho do vídeo
                bg_music = bg_music.with_duration(duration)
                
                # Mixagem: Voz (100%) + Fundo (10%)
                final_audio = CompositeAudioClip([speech_audio, bg_music])
                print(f"🎵 Música de fundo adicionada: {os.path.basename(bg_music_path)}")
            except Exception as e:
                print(f"⚠️ Erro ao adicionar música de fundo: {e}")
        else:
             print(f"⚠️ Música de fundo não encontrada em: {bg_music_path}")

        final_output = final_video.with_audio(final_audio)
        
        # 6. Salvar Vídeo
        # Sanitiza nome do arquivo (remove caracteres inválidos como |)
        safe_title = titulo.replace("|", "").replace(":", "").replace("/", "").strip()
        output_filename = f"{idioma}_{safe_title}_{index}.mp4".replace(" ", "_")
        output_path = os.path.join(output_dir, output_filename)
        
        final_output.with_fps(CONFIG["FPS"]).write_videofile(
            output_path, 
            codec='libx264', 
            audio_codec='aac', 
            preset='ultrafast',
            threads=4,
            logger=None
        )
        print(f"✅ Vídeo salvo: {output_path}")

        # 7. Salvar Thumbnail (Capa)
        thumb_filename = f"{idioma}_{safe_title}_{index}_thumb.jpg".replace(" ", "_")
        thumb_path = os.path.join(output_dir, thumb_filename)
        try:
            # Pega o frame em 1.0s
            frame = final_output.get_frame(1.0)
            # Converte Array -> Imagem PIL -> RGB (remove transparência) -> Salva
            img_thumb = Image.fromarray(frame).convert("RGB")
            img_thumb.save(thumb_path, quality=95)
            print(f"🖼️ Thumbnail salva: {thumb_path}")
        except Exception as e:
            print(f"Erro ao salvar thumbnail: {e}")

    print("\n--- Processamento Completo! ---")

if __name__ == "__main__":
    asyncio.run(processar_roteiro())
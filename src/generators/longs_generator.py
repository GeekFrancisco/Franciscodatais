import os
import sys
import random
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import asyncio
import pandas as pd
from PIL import Image
from moviepy import CompositeVideoClip, ImageClip, AudioFileClip, CompositeAudioClip, concatenate_audioclips, concatenate_videoclips, VideoClip, AudioClip
import numpy as np

from src.configs.settings import ASSETS_DIR, TEMP_AUDIO_DIR, OUTPUT_LONGS, INPUT_IMAGES_LONGS, EXCEL_PATH
from src.configs.longs import LONGS_CONFIG
from src.utils.video_utils import create_text_image, create_vignette_overlay, create_thumbnail, apply_ken_burns_effect
from src.utils.audio_utils import generate_audio_and_word_timings, estimate_word_timings, generate_bell_sfx, get_audio_duration
from moviepy.video.fx import FadeOut, FadeIn, Margin
# Tenta importar efeitos de cor (MoviePy v1 vs v2)
try:
    from moviepy.video.fx import colorx, lum_contrast
except ImportError:
    try:
        from moviepy.video.fx.all import colorx, lum_contrast
    except ImportError:
        colorx = None
        lum_contrast = None

from moviepy.audio.fx import AudioFadeIn, AudioFadeOut


def create_static_slide(image_path, duration):
    try:
        original_img = Image.open(image_path).convert('RGB')
    except Exception:
        return None

    target_ratio = LONGS_CONFIG["WIDTH"] / LONGS_CONFIG["HEIGHT"]
    img_ratio = original_img.width / original_img.height

    if img_ratio > target_ratio:
        # Imagem mais larga que o alvo (ou igual) -> ajusta pela altura
        base_h = LONGS_CONFIG["HEIGHT"]
        base_w = int(base_h * img_ratio)
    else:
        # Imagem mais alta que o alvo -> ajusta pela largura
        base_w = LONGS_CONFIG["WIDTH"]
        base_h = int(base_w / img_ratio)

    # Redimensiona (LANCZOS para qualidade)
    resized = original_img.resize((base_w, base_h), Image.LANCZOS)
    
    # Corta o centro exato (Crop Center)
    left = (base_w - LONGS_CONFIG["WIDTH"]) / 2
    top = (base_h - LONGS_CONFIG["HEIGHT"]) / 2
    right = left + LONGS_CONFIG["WIDTH"]
    bottom = top + LONGS_CONFIG["HEIGHT"]
    
    cropped = resized.crop((left, top, right, bottom))
    
    # Cria ImageClip estático
    clip = ImageClip(np.array(cropped)).with_duration(duration)
    return clip


def create_slideshow_clip(img_dir, total_duration):
    if not os.path.exists(img_dir):
        print(f"❌ ERRO: Diretório de imagens não encontrado: {img_dir}")
        return None

    valid_images = [
        os.path.join(img_dir, f)
        for f in os.listdir(img_dir)
        if f.lower().endswith(('.jpg', '.png', '.jpeg'))
    ]
    if not valid_images:
        print(f"❌ ERRO: Nenhuma imagem encontrada em {img_dir} para o slideshow!")
        return VideoClip(
            lambda t: np.zeros(
                (LONGS_CONFIG["HEIGHT"], LONGS_CONFIG["WIDTH"], 3), dtype=np.uint8
            ),
            duration=total_duration,
        )

    clips = []
    current_duration = 0
    img_idx = 0

    while current_duration < total_duration:
        remaining = total_duration - current_duration
        clip_dur = min(LONGS_CONFIG["SLIDE_DURATION"], remaining)

        img_path = valid_images[img_idx % len(valid_images)]
        
        # Tenta usar Ken Burns (Zoom/Pan) para maior retenção
        # Se falhar, usa o slide estático como fallback
        try:
            # Prompt: Slow Zoom-In de 1.0 a 1.15 (Progressivo Lento)
            clip = apply_ken_burns_effect(
                img_path, 
                LONGS_CONFIG["WIDTH"], 
                LONGS_CONFIG["HEIGHT"], 
                clip_dur,
                zoom_range=(1.0, 1.15),
                pan_range=0.03,
                force_mode='zoom_in' # Garante Zoom In consistente
            )
        except Exception as e:
            print(f"⚠️ Erro no Ken Burns para {img_path}: {e}. Usando estático.")
            clip = None

        if clip is None:
             clip = create_static_slide(img_path, clip_dur)

        if clip:
            clips.append(clip)
            current_duration += clip_dur
            img_idx += 1
        else:
            img_idx += 1

    return concatenate_videoclips(clips, method="compose")


async def process_longs_from_excel(preview=True):
    excel_path = EXCEL_PATH
    if not os.path.exists(excel_path):
        print(f"ERRO: Arquivo Excel não encontrado em {excel_path}")
        print("Certifique-se de que o arquivo 'Roteiro_Geral.xlsx' existe na raiz do projeto.")
        return

    try:
        df = pd.read_excel(excel_path, sheet_name='Longos')
    except ValueError as e:
        print(f"ERRO: Aba 'Longos' não encontrada no arquivo Excel. Detalhes: {e}")
        return
    except Exception as e:
        print(f"ERRO ao ler Excel: {e}")
        return

    print(f"Encontrados {len(df)} vídeos para gerar (Longos).")

    os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)
    os.makedirs(OUTPUT_LONGS, exist_ok=True)

    for index, row in df.iterrows():
        try:
            print(f"\n--- Processando Longo {index + 1}/{len(df)} ---")

            idioma = row['Idioma'].strip().upper()
            texto = row['Texto']
            titulo = str(row['Titulo'])
            subtitulo = str(row.get('Subtitulo', ''))

            tema_visual = str(row.get('TemaVisual', '')).strip()

            texto_thumb = str(row.get('TextoThumb', '')).strip()
            if not texto_thumb or texto_thumb.lower() == 'nan':
                texto_thumb = titulo
            
            imagem_thumb_nome = str(row.get('ImagemThumb', '')).strip()
            if imagem_thumb_nome.lower() == 'nan': imagem_thumb_nome = ""

            marca_dagua = str(row.get('MarcaDagua', '')).strip()
            if marca_dagua.lower() == 'nan':
                marca_dagua = ""

            hook_text = str(row.get('Hook', '')).strip()
            if hook_text.lower() == 'nan': hook_text = ""

            voice = LONGS_CONFIG.get(f"VOICE_{idioma}", LONGS_CONFIG["VOICE_EN"])
            audio_filename = f"long_audio_{index}.mp3"
            audio_path = os.path.join(TEMP_AUDIO_DIR, audio_filename)

            print("🎤 Gerando áudio (Longo) com pausas de meditação...")
            
            # Split text into sentences for meditation pauses (1.5s)
            sentences = re.split(r'(?<=[.!?])\s+', texto)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if not sentences: sentences = [texto]
            
            final_audio_clips = []
            final_word_timings = []
            current_offset = 0.0
            pause_duration = 1.5
            
            # Helper to create silent audio
            def make_silence(dur):
                return AudioClip(lambda t: [0]*2, duration=dur, fps=44100) # Stereo silence

            for i, sent in enumerate(sentences):
                sent_filename = f"long_audio_{index}_part_{i}.mp3"
                sent_path = os.path.join(TEMP_AUDIO_DIR, sent_filename)
                
                # Reuse existing generation logic
                w_timings = await generate_audio_and_word_timings(sent, voice, sent_path, LONGS_CONFIG.get("VOICE_RATE", "-10%"))
                
                if w_timings is not None and os.path.exists(sent_path):
                    clip = AudioFileClip(sent_path)
                    final_audio_clips.append(clip)
                    
                    # Adjust timings
                    for w in w_timings:
                        w['start'] += current_offset
                        w['end'] += current_offset
                        final_word_timings.append(w)
                    
                    current_offset += clip.duration
                    
                    # Add pause if not last sentence
                    if i < len(sentences) - 1:
                        final_audio_clips.append(make_silence(pause_duration))
                        current_offset += pause_duration
                else:
                    print(f"⚠️ Falha ao gerar áudio para sentença {i}: {sent[:30]}...")
            
            word_timings = []
            if final_audio_clips:
                print(f"   Concatenando {len(final_audio_clips)} clipes (frases + pausas)...")
                final_audio_clip = concatenate_audioclips(final_audio_clips)
                final_audio_clip.write_audiofile(audio_path, fps=44100)
                word_timings = final_word_timings
            else:
                 print("⚠️ Falha na geração por frases. Tentando modo bloco único.")
                 word_timings = await generate_audio_and_word_timings(texto, voice, audio_path, LONGS_CONFIG.get("VOICE_RATE", "-10%"))

            audio_ok = os.path.exists(audio_path) and os.path.getsize(audio_path) > 1000
            if not audio_ok:
                print("⚠️ Áudio da narração não foi gerado corretamente (talvez sem internet). Vídeo será gerado sem voz.")
                word_timings = []

            if not word_timings and audio_ok:
                duration = get_audio_duration(audio_path)
                word_timings = estimate_word_timings(texto, duration)
            elif word_timings:
                duration = word_timings[-1]["end"]
            else:
                duration = 60.0

            padding_start = LONGS_CONFIG.get("PADDING_START", 2.0)
            padding_end = LONGS_CONFIG.get("PADDING_END", 3.0)
            duration += padding_start + padding_end

            if preview:
                print("🚧 MODO PREVIEW: Limitando para 30 segundos.")
                if word_timings:
                    word_timings = [w for w in word_timings if w["end"] < (30.0 - padding_end)]
                duration = 30.0

            print(f"⏱️ Duração total: {duration:.2f}s")

            print("🖼️ Montando Slideshow...")
            current_img_dir = INPUT_IMAGES_LONGS
            if tema_visual and tema_visual.lower() != 'nan':
                possible_dir = os.path.join(INPUT_IMAGES_LONGS, tema_visual)
                if os.path.exists(possible_dir):
                    current_img_dir = possible_dir
                    print(f"📂 Usando tema visual: {tema_visual}")
                else:
                    print(f"⚠️ Tema visual '{tema_visual}' não encontrado, usando padrão.")

            base_clip = create_slideshow_clip(current_img_dir, duration)
            if base_clip is None:
                continue

            # Color Grading (Saturação + Contraste)
            if colorx and lum_contrast:
                print("   [Visual] Aplicando Color Grading (Saturação + Contraste)...")
                base_clip = base_clip.with_effects([colorx(1.2), lum_contrast(contrast=0.1)])
            
            vignette = create_vignette_overlay(LONGS_CONFIG["WIDTH"], LONGS_CONFIG["HEIGHT"], duration)

            clips_to_add = []

            if marca_dagua:
                # User requested smaller watermark and top-left position
                wm_img = create_text_image(
                    marca_dagua,
                    LONGS_CONFIG["WIDTH"],
                    LONGS_CONFIG["FONT_PATH"],
                    30, # Smaller font size (was default/40)
                    LONGS_CONFIG["COLOR_WATERMARK"],
                    bg_color=None,
                    align='center',
                    stroke_width=2,
                    stroke_fill='black'
                )
                wm_clip = ImageClip(wm_img).with_position(('left', 'top')).with_opacity(0.7).with_duration(duration)
                wm_clip = wm_clip.with_position((50, 50)) # Top Left with padding
                clips_to_add.append(wm_clip)

            # Define tempos do CTA (Subscribe) antecipadamente para evitar sobreposição
            subscribe_text = LONGS_CONFIG["SUBSCRIBE_TEXTS"].get(idioma, "SUBSCRIBE")
            cta_start_time = max(0, duration - padding_end - 4.0) # CTA dura 4s
            cta_duration = 4.0

            title_img = create_text_image(
                titulo.upper(),
                LONGS_CONFIG["WIDTH"],
                LONGS_CONFIG["FONT_PATH"],
                LONGS_CONFIG["FONT_SIZE_TITLE_MAIN"],
                LONGS_CONFIG["COLOR_TITLE"],
                stroke_width=6
            )
            # Raised title position (was 200) - Agora encerra quando começa o CTA
            title_clip = ImageClip(title_img).with_position(('center', 150)).with_start(0).with_end(cta_start_time)
            clips_to_add.append(title_clip)

            if subtitulo and subtitulo.lower() != 'nan':
                sub_img = create_text_image(
                    subtitulo,
                    LONGS_CONFIG["WIDTH"],
                    LONGS_CONFIG["FONT_PATH"],
                    LONGS_CONFIG["FONT_SIZE_TITLE_SECONDARY"],
                    LONGS_CONFIG["COLOR_TITLE_SECONDARY"]
                )
                # Raised subtitle position (was 350) - Renomeado para evitar conflito e encerra no CTA
                subtitle_clip = ImageClip(sub_img).with_position(('center', 280)).with_start(0).with_end(cta_start_time)
                clips_to_add.append(subtitle_clip)

            # CTA (Subscribe)
            cta_img = create_text_image(
                subscribe_text,
                LONGS_CONFIG["WIDTH"],
                LONGS_CONFIG["FONT_PATH"],
                90,
                "#FF0000",
                bg_color=(255, 255, 255, 200),
                stroke_width=2
            )
            
            cta_clip = ImageClip(cta_img).with_position('center').with_start(cta_start_time).with_duration(cta_duration)
            cta_clip = cta_clip.with_effects([FadeIn(0.5), FadeOut(0.5)])
            clips_to_add.append(cta_clip)

            offset = LONGS_CONFIG.get("SUBTITLE_OFFSET", 0)
            for w in word_timings:
                w["start"] += padding_start + offset
                w["end"] += padding_start + offset
                w["start"] = max(0, w["start"])
                w["end"] = max(0, w["end"])

            if word_timings:
                print("   [Legendas] Gerando legendas meditativas (Fade In/Out)...")
                words_per_chunk = 5
                chunk = []
                for i, item in enumerate(word_timings):
                    chunk.append(item)
                    if len(chunk) >= words_per_chunk or i == len(word_timings) - 1:
                        start_t = chunk[0]["start"]
                        end_t = chunk[-1]["end"]
                        text_chunk = " ".join([c["word"] for c in chunk])

                        # Ajuste visual: Fonte Bold (se disponível) e maior
                        font_p = LONGS_CONFIG.get("FONT_PATH_BOLD", LONGS_CONFIG["FONT_PATH"])
                        
                        txt_img = create_text_image(
                            text_chunk,
                            LONGS_CONFIG["WIDTH"],
                            font_p,
                            70, # Tamanho 70 para estilo meditativo
                            "#FFFFFF",
                            bg_color=None,
                            stroke_width=2, 
                            stroke_fill='black',
                            shadow=True
                        )
                        
                        txt_clip = ImageClip(txt_img).with_position(('center', 850)).with_start(start_t).with_end(end_t)
                        
                        # Aplica Fade In/Out suave (0.8s)
                        fade_dur = 0.8
                        txt_clip = txt_clip.with_effects([FadeIn(fade_dur), FadeOut(fade_dur)])
                        
                        clips_to_add.append(txt_clip)
                        chunk = []

            main_video = CompositeVideoClip([base_clip, vignette] + clips_to_add)

            if audio_ok:
                voice_clip = AudioFileClip(audio_path).with_start(padding_start)

                # --- AUDIO LAYERING (Nature + Pads) ---
                bg_tracks = []
                
                # 1. Nature Sounds (-25dB) - Vento e Pássaros
                nature_file = os.path.join(ASSETS_DIR, "nature_ambience.mp3")
                # Fallback: se não existir, tenta achar qualquer mp3 com 'nature' ou 'wind' no nome
                if not os.path.exists(nature_file):
                    for f in os.listdir(ASSETS_DIR):
                        if "nature" in f.lower() or "wind" in f.lower() or "passaros" in f.lower():
                            nature_file = os.path.join(ASSETS_DIR, f)
                            break
                            
                if os.path.exists(nature_file):
                    print(f"   [Soundscape] Adicionando Natureza (Vento/Pássaros): {os.path.basename(nature_file)}")
                    nature_clip = AudioFileClip(nature_file)
                    loops_nature = int(duration / nature_clip.duration) + 1
                    nature_clip = concatenate_audioclips([nature_clip] * loops_nature).with_duration(duration)
                    nature_clip = nature_clip.with_volume_scaled(0.06) # ~ -25dB (era 0.08/-22dB)
                    nature_clip = nature_clip.with_effects([AudioFadeIn(2.0), AudioFadeOut(3.0)])
                    bg_tracks.append(nature_clip)
                else:
                    print("⚠️ Arquivo de Natureza (nature_ambience.mp3) não encontrado. Pulei camada.")

                # 2. Pads Atmosféricos (-18dB)
                bg_music_clip = None
                try:
                    # Tenta encontrar o arquivo de Pads na pasta assets
                    pads_file = os.path.join(ASSETS_DIR, "Pulsar - The Grey Room _ Density & Time.mp3")
                    if not os.path.exists(pads_file):
                         # Tenta qualquer mp3 na pasta assets se o específico não existir
                         files = [f for f in os.listdir(ASSETS_DIR) if f.endswith(".mp3") and "subscribe" not in f.lower() and "nature" not in f.lower()]
                         if files:
                             pads_file = os.path.join(ASSETS_DIR, files[0])
                    
                    if os.path.exists(pads_file):
                        print(f"   [Soundscape] Adicionando pads: {os.path.basename(pads_file)}")
                        bg_music = AudioFileClip(pads_file)
                        
                        # Loop manual seguro
                        loops_needed = int(duration / bg_music.duration) + 1
                        bg_music = concatenate_audioclips([bg_music] * loops_needed)
                        bg_music = bg_music.with_duration(duration)
                        
                        # Volume: -18dB (~0.12)
                        bg_music = bg_music.with_volume_scaled(0.12)
                        
                        # Fade In/Out para suavidade
                        bg_music = bg_music.with_effects([AudioFadeIn(2.0), AudioFadeOut(3.0)])
                        
                        bg_tracks.append(bg_music)
                    else:
                        print("⚠️ Arquivo de Pads (Soundscape) não encontrado em assets.")
                except Exception as e:
                    print(f"⚠️ Erro ao adicionar Soundscape: {e}")

                sfx_audio = None
                try:
                    sfx_filename = "bell_sfx.wav"
                    sfx_path_full = os.path.join(TEMP_AUDIO_DIR, sfx_filename)
                    generate_bell_sfx(sfx_path_full)
                    if os.path.exists(sfx_path_full):
                        sfx_clip = AudioFileClip(sfx_path_full).with_start(cta_start_time)
                        sfx_audio = sfx_clip
                except Exception as e:
                    print(f"⚠️ Erro ao gerar SFX: {e}")

                audio_tracks = [voice_clip]
                audio_tracks.extend(bg_tracks)
                
                if sfx_audio:
                    audio_tracks.append(sfx_audio)

                main_audio = CompositeAudioClip(audio_tracks)
                main_video = main_video.with_audio(main_audio)

            print("️ Gerando Intro (Thumbnail)...")
            
            thumb_base_img = None
            
            # 1. Tenta imagem específica da coluna ImagemThumb
            if imagem_thumb_nome:
                # Procura em INPUT_IMAGES_LONGS geral ou dentro da pasta do tema?
                # Assumindo que pode estar na pasta do tema ou na raiz de INPUT_IMAGES_LONGS
                possible_paths = [
                    os.path.join(current_img_dir, imagem_thumb_nome),
                    os.path.join(INPUT_IMAGES_LONGS, imagem_thumb_nome)
                ]
                for p in possible_paths:
                    if os.path.exists(p):
                        thumb_base_img = p
                        print(f"   [Thumb] Usando imagem específica: {imagem_thumb_nome}")
                        break
            
            # 2. Se não achou, pega a primeira do slideshow
            if not thumb_base_img:
                valid_images = [os.path.join(current_img_dir, f) for f in os.listdir(current_img_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
                thumb_base_img = valid_images[0] if valid_images else None
                if thumb_base_img:
                    print(f"   [Thumb] Usando primeira imagem do slideshow: {os.path.basename(thumb_base_img)}")

            final_video = main_video

            if thumb_base_img:
                thumb_path = os.path.join(OUTPUT_LONGS, f"thumb_{index}.jpg")
                create_thumbnail(
                    thumb_base_img,
                    texto_thumb,
                    thumb_path,
                    LONGS_CONFIG["WIDTH"],
                    LONGS_CONFIG["HEIGHT"],
                    LONGS_CONFIG["FONT_PATH"],
                    watermark=marca_dagua
                )

                intro_duration = LONGS_CONFIG.get("THUMB_INTRO_DURATION", 2.0)
                
                # Intro com Movimento (Zoom In Suave) para não ser estática
                # Usa a própria thumbnail gerada como input para o Ken Burns
                try:
                    intro_clip = apply_ken_burns_effect(
                        thumb_path,
                        LONGS_CONFIG["WIDTH"],
                        LONGS_CONFIG["HEIGHT"],
                        intro_duration,
                        zoom_range=(1.0, 1.1), # Consistente com o resto
                        pan_range=0.0 # Sem pan na intro
                    )
                except:
                    intro_clip = None
                
                if intro_clip is None:
                    intro_clip = ImageClip(thumb_path).with_duration(intro_duration)

                intro_clip = intro_clip.with_effects([FadeOut(1.0)])
                final_video = final_video.with_effects([FadeIn(1.0)])
                final_video = concatenate_videoclips([intro_clip, final_video])

            # --- HOOK (Convite à Paz) ---
            # Inserido ANTES de tudo (antes até da thumbnail intro, se fizer sentido, ou depois)
            # O usuário pediu "clipe inicial de 5 segundos... antes de começar a oração principal".
            # Vamos colocar: Hook (5s) -> IntroThumb (2s) -> Oração.
            if hook_text:
                print(f"   [Hook] Gerando clipe inicial de 5s: {hook_text}")
                
                # Fundo do Hook: Imagem borrada ou cor sólida
                hook_bg = None
                if thumb_base_img and os.path.exists(thumb_base_img):
                     try:
                         pil_img = Image.open(thumb_base_img).convert('RGB')
                         pil_img = pil_img.resize((LONGS_CONFIG["WIDTH"], LONGS_CONFIG["HEIGHT"]), Image.LANCZOS)
                         pil_img = pil_img.filter(ImageFilter.GaussianBlur(radius=20))
                         # Darken
                         enhancer = ImageEnhance.Brightness(pil_img)
                         pil_img = enhancer.enhance(0.4) 
                         hook_bg = ImageClip(np.array(pil_img)).with_duration(5.0)
                     except:
                         pass
                
                if hook_bg is None:
                    hook_bg = ColorClip(size=(LONGS_CONFIG["WIDTH"], LONGS_CONFIG["HEIGHT"]), color=(20, 20, 30), duration=5.0)

                # Texto do Hook
                hook_txt_img = create_text_image(
                    hook_text,
                    LONGS_CONFIG["WIDTH"],
                    LONGS_CONFIG["FONT_PATH"],
                    90, # Tamanho legível
                    "#FFFFFF",
                    align='center',
                    stroke_width=1,
                    shadow=True
                )
                hook_txt_clip = ImageClip(hook_txt_img).with_position('center').with_duration(5.0)
                
                # Efeito Fade In/Out no texto
                hook_txt_clip = hook_txt_clip.with_effects([FadeIn(1.0), FadeOut(1.0)])
                
                hook_clip = CompositeVideoClip([hook_bg, hook_txt_clip])
                
                # Adiciona à cadeia final
                final_video = concatenate_videoclips([hook_clip, final_video])

            # Música de fundo para oração (Suave e Emotiva)
            # Substituindo 'Pulsar' por algo mais calmo se disponível, ou ajustando volume
            bg_music_path = os.path.join(ASSETS_DIR, "ambient_prayer_loop.mp3")
            if not os.path.exists(bg_music_path):
                 # Fallback para a música padrão, mas com volume BEM BAIXO
                 bg_music_path = os.path.join(ASSETS_DIR, "Pulsar - The Grey Room _ Density & Time.mp3")

            if audio_ok and os.path.exists(bg_music_path):
                total_duration = final_video.duration
                bg_music = AudioFileClip(bg_music_path)
                
                # Loop da música
                bg_music = concatenate_audioclips([bg_music] * (int(total_duration // bg_music.duration) + 1))
                bg_music = bg_music.with_duration(total_duration)

                # --- MIXAGEM DE ÁUDIO (-18dB vs Voz) e FADE OUT FINAL (3s) ---
                print("   [Audio] Aplicando mixagem (-18dB) e fade out final...")
                try:
                    # -18dB ~= 0.12 (12%)
                    bg_music = bg_music.with_volume_scaled(0.12)
                    bg_music = bg_music.with_effects([AudioFadeOut(duration=3.0)])
                except Exception as e:
                    print(f"⚠️ Erro ao aplicar efeitos de áudio: {e}")
                    bg_music = bg_music.with_volume_scaled(0.12) # Fallback seguro

                existing_audio = final_video.audio
                if existing_audio is not None:
                    final_audio = CompositeAudioClip([bg_music, existing_audio])
                else:
                    final_audio = bg_music
                final_video = final_video.with_audio(final_audio)

            safe_title = "".join([c for c in titulo if c.isalnum() or c in (' ', '_')]).strip().replace(" ", "_")
            out_filename = f"LONG_{idioma}_{safe_title}.mp4"
            out_path = os.path.join(OUTPUT_LONGS, out_filename)

            print(f"💾 Salvando Longo em: {out_path}")
            final_video.write_videofile(out_path, fps=LONGS_CONFIG["FPS"], codec='libx264', audio_codec='aac')

        except Exception as e:
            print(f"❌ Erro ao processar linha {index}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    preview = True
    args = sys.argv[1:]

    if "--full" in args or "--no-preview" in args:
        preview = False
    elif "--preview" in args:
        preview = True
    else:
        print("=== GERADOR DE LONGOS ===")
        print("Escolha o modo de execução:")
        print("  1) Preview RÁPIDO (~30s) para testar layout/legendas")
        print("  2) FULL (duração completa da narração)")
        escolha = input("Digite 1 ou 2 e pressione ENTER [1]: ").strip()
        if escolha == "2":
            preview = False
        else:
            preview = True

    asyncio.run(process_longs_from_excel(preview))

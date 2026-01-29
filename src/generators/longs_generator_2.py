import os
import sys
import random
import asyncio
import pandas as pd
import numpy as np
from PIL import Image

from moviepy import (
    CompositeVideoClip, ImageClip, AudioFileClip,
    CompositeAudioClip, concatenate_audioclips,
    concatenate_videoclips, VideoClip
)
from moviepy.video.fx import FadeOut, FadeIn

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.configs.settings import (
    ASSETS_DIR, TEMP_AUDIO_DIR, OUTPUT_LONGS,
    INPUT_IMAGES_LONGS, EXCEL_PATH
)
from src.configs.longs import LONGS_CONFIG
from src.utils.video_utils import (
    create_text_image, create_vignette_overlay,
    create_thumbnail, apply_ken_burns_effect
)
from src.utils.audio_utils import (
    generate_audio_and_word_timings, estimate_word_timings,
    generate_bell_sfx, get_audio_duration
)

# ===============================
# CONFIG EXTRA (SEGURANÇA)
# ===============================
LONGS_CONFIG.setdefault("REPEAT_PRAYER", True)
LONGS_CONFIG.setdefault("REPEAT_OFFSET_RATIO", 0.6)
LONGS_CONFIG.setdefault("WORDS_PER_CHUNK", 6)
LONGS_CONFIG.setdefault("SUBTITLE_Y", 850)
LONGS_CONFIG.setdefault("DUCK_BG_MUSIC", 0.08)
LONGS_CONFIG.setdefault("VOICE_VOLUME", 1.0)

# ===============================
# CACHE DE TEXTO (PERFORMANCE)
# ===============================
TEXT_CACHE = {}

def cached_text_image(text, *args, **kwargs):
    key = (text,) + args + tuple(kwargs.items())
    if key not in TEXT_CACHE:
        TEXT_CACHE[key] = create_text_image(text, *args, **kwargs)
    return TEXT_CACHE[key]

# ===============================
# SUBTÍTULO POR PONTUAÇÃO
# ===============================
def chunk_by_punctuation(word_timings, max_words=6):
    chunks, chunk = [], []
    for w in word_timings:
        chunk.append(w)
        if (
            len(chunk) >= max_words or
            w["word"].endswith(('.', ',', ';', ':', '?', '!'))
        ):
            chunks.append(chunk)
            chunk = []
    if chunk:
        chunks.append(chunk)
    return chunks

# ===============================
# SLIDE ESTÁTICO (FALLBACK)
# ===============================
def create_static_slide(image_path, duration):
    try:
        img = Image.open(image_path).convert("RGB")
    except Exception:
        return None

    target_ratio = LONGS_CONFIG["WIDTH"] / LONGS_CONFIG["HEIGHT"]
    img_ratio = img.width / img.height

    if img_ratio > target_ratio:
        h = LONGS_CONFIG["HEIGHT"]
        w = int(h * img_ratio)
    else:
        w = LONGS_CONFIG["WIDTH"]
        h = int(w / img_ratio)

    img = img.resize((w, h), Image.LANCZOS)

    left = (w - LONGS_CONFIG["WIDTH"]) // 2
    top = (h - LONGS_CONFIG["HEIGHT"]) // 2
    img = img.crop((left, top, left + LONGS_CONFIG["WIDTH"], top + LONGS_CONFIG["HEIGHT"]))

    return ImageClip(np.array(img)).with_duration(duration)

# ===============================
# SLIDESHOW
# ===============================
def create_slideshow_clip(img_dir, total_duration):
    images = [
        os.path.join(img_dir, f)
        for f in os.listdir(img_dir)
        if f.lower().endswith((".jpg", ".png", ".jpeg"))
    ]

    if not images:
        return VideoClip(
            lambda t: np.zeros((LONGS_CONFIG["HEIGHT"], LONGS_CONFIG["WIDTH"], 3), dtype=np.uint8),
            duration=total_duration
        )

    clips, t, idx = [], 0, 0
    while t < total_duration:
        dur = min(LONGS_CONFIG["SLIDE_DURATION"], total_duration - t)
        path = images[idx % len(images)]

        try:
            clip = apply_ken_burns_effect(
                path,
                LONGS_CONFIG["WIDTH"],
                LONGS_CONFIG["HEIGHT"],
                dur,
                zoom_speed=LONGS_CONFIG.get("ZOOM_SPEED", 0.005),
                pan_speed=LONGS_CONFIG.get("PAN_SPEED", 1)
            )
        except:
            clip = create_static_slide(path, dur)

        if clip:
            clips.append(clip)
            t += dur

        idx += 1

    return concatenate_videoclips(clips, method="compose")

# ===============================
# PIPELINE PRINCIPAL
# ===============================
async def process_longs_from_excel(preview=True):
    df = pd.read_excel(EXCEL_PATH, sheet_name="Longos")

    os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)
    os.makedirs(OUTPUT_LONGS, exist_ok=True)

    for i, row in df.iterrows():
        print(f"\n▶ Gerando vídeo {i+1}/{len(df)}")

        idioma = str(row["Idioma"]).upper()
        texto = row["Texto"]
        titulo = str(row["Titulo"])

        voice = LONGS_CONFIG.get(f"VOICE_{idioma}", LONGS_CONFIG["VOICE_EN"])
        audio_path = os.path.join(TEMP_AUDIO_DIR, f"audio_{i}.mp3")

        word_timings = await generate_audio_and_word_timings(
            texto, voice, audio_path, LONGS_CONFIG.get("VOICE_RATE", "-10%")
        )

        audio_ok = os.path.exists(audio_path)
        if not word_timings and audio_ok:
            duration = get_audio_duration(audio_path)
            word_timings = estimate_word_timings(texto, duration)
        else:
            duration = word_timings[-1]["end"] if word_timings else 60

        padding_start = LONGS_CONFIG.get("PADDING_START", 2)
        padding_end = LONGS_CONFIG.get("PADDING_END", 3)
        duration += padding_start + padding_end

        if preview:
            duration = 30
            word_timings = [w for w in word_timings if w["end"] < 27]

        base_clip = create_slideshow_clip(INPUT_IMAGES_LONGS, duration)
        vignette = create_vignette_overlay(LONGS_CONFIG["WIDTH"], LONGS_CONFIG["HEIGHT"], duration)

        clips = []

        # ===== SUBTÍTULOS NORMAIS =====
        for w in word_timings:
            w["start"] += padding_start
            w["end"] += padding_start

        chunks = chunk_by_punctuation(word_timings, LONGS_CONFIG["WORDS_PER_CHUNK"])

        for c in chunks:
            img = cached_text_image(
                " ".join(w["word"] for w in c),
                LONGS_CONFIG["WIDTH"],
                LONGS_CONFIG["FONT_PATH"],
                LONGS_CONFIG["FONT_SIZE_SUBTITLE"],
                "#FFFFFF",
                stroke_width=3,
                stroke_fill="black"
            )
            clips.append(
                ImageClip(img)
                .with_start(c[0]["start"])
                .with_end(c[-1]["end"])
                .with_position(("center", LONGS_CONFIG["SUBTITLE_Y"]))
            )

        # ===== REPETIÇÃO GUIADA =====
        if LONGS_CONFIG["REPEAT_PRAYER"]:
            offset = duration * LONGS_CONFIG["REPEAT_OFFSET_RATIO"]
            for c in chunks:
                s = c[0]["start"] + offset
                e = c[-1]["end"] + offset
                if s >= duration:
                    continue
                img = cached_text_image(
                    " ".join(w["word"] for w in c),
                    LONGS_CONFIG["WIDTH"],
                    LONGS_CONFIG["FONT_PATH"],
                    LONGS_CONFIG["FONT_SIZE_SUBTITLE"],
                    "#EAEAEA",
                    stroke_width=3,
                    stroke_fill="black"
                )
                clips.append(
                    ImageClip(img)
                    .with_start(s)
                    .with_end(min(e, duration))
                    .with_opacity(0.85)
                    .with_position(("center", LONGS_CONFIG["SUBTITLE_Y"]))
                )

        video = CompositeVideoClip([base_clip, vignette] + clips)

        # ===== ÁUDIO =====
        if audio_ok:
            voice_clip = AudioFileClip(audio_path).with_start(padding_start)
            bg_music_path = os.path.join(ASSETS_DIR, "ambient_prayer_loop.mp3")

            if os.path.exists(bg_music_path):
                bg = AudioFileClip(bg_music_path)
                bg = bg.with_volume_scaled(LONGS_CONFIG["DUCK_BG_MUSIC"]).audio_fadein(2).audio_fadeout(3)
                bg = concatenate_audioclips([bg] * (int(video.duration // bg.duration) + 1)).with_duration(video.duration)

                video = video.with_audio(
                    CompositeAudioClip([
                        bg,
                        voice_clip.with_volume_scaled(LONGS_CONFIG["VOICE_VOLUME"])
                    ])
                )
            else:
                video = video.with_audio(voice_clip)

        out = os.path.join(OUTPUT_LONGS, f"LONG_{idioma}_{i}.mp4")
        video.write_videofile(out, fps=LONGS_CONFIG["FPS"], codec="libx264", audio_codec="aac")

        # ===== LIMPEZA =====
        video.close()
        if audio_ok:
            voice_clip.close()

# ===============================
# MAIN
# ===============================
if __name__ == "__main__":
    preview = "--full" not in sys.argv
    asyncio.run(process_longs_from_excel(preview))

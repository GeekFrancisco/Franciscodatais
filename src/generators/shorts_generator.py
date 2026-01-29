import os
import sys

"""
Gerador de vídeos Shorts (9:16) a partir da aba 'Shorts' do Roteiro_Geral.xlsx.

Responsabilidades principais:
- Ler a planilha única configurada em EXCEL_PATH (aba 'Shorts').
- Gerar áudio TTS com Edge-TTS e calcular tempos por palavra.
- Montar o vídeo com efeito Ken Burns, textos, legendas e CTA.
- Criar thumbnail de abertura e salvar o vídeo final na pasta de saída.
"""

# Adiciona o diretório raiz ao sys.path para permitir importações do módulo 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import asyncio
import random
from datetime import datetime
import pandas as pd
from moviepy import CompositeVideoClip, ImageClip, AudioFileClip, CompositeAudioClip, concatenate_audioclips, concatenate_videoclips
from moviepy.video.fx import Resize
from src.configs.settings import ASSETS_DIR, TEMP_AUDIO_DIR, OUTPUT_SHORTS, INPUT_IMAGES_SHORTS, EXCEL_PATH
from src.configs.shorts import SHORTS_CONFIG
from src.utils.video_utils import create_text_image, apply_ken_burns_effect, create_vignette_overlay, create_thumbnail
from src.utils.audio_utils import generate_audio_and_word_timings, estimate_word_timings, generate_bell_sfx, get_audio_duration

# SUBSCRIBE_TEXTS removido (agora em SHORTS_CONFIG)


async def process_shorts_from_excel(only_indices=None):
    """
    Lê a aba 'Shorts' do Excel e gera vídeos verticais.

    Parâmetros:
        only_indices (set[int] | None):
            - None  -> processa todas as linhas da aba.
            - set() -> processa apenas os índices informados (1-based).
    """
    excel_path = EXCEL_PATH
    if not os.path.exists(excel_path):
        print(f"ERRO: Arquivo Excel não encontrado em {excel_path}")
        print("Certifique-se de que o arquivo 'Roteiro_Geral.xlsx' existe na raiz do projeto.")
        return

    try:
        # Lê especificamente a aba 'Shorts' (evita ambiguidades com outras abas)
        df = pd.read_excel(excel_path, sheet_name='Shorts')
    except ValueError as e:
        print(f"ERRO: Aba 'Shorts' não encontrada no arquivo Excel. Detalhes: {e}")
        return
    except Exception as e:
        print(f"ERRO ao ler Excel: {e}")
        return

    print(f"Encontrados {len(df)} vídeos para gerar (Shorts).")

    # Garante diretórios de trabalho (áudios temporários e saída de vídeos)
    os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)
    os.makedirs(OUTPUT_SHORTS, exist_ok=True)

    # Itera linha a linha da planilha; index é 0-based, short_number é 1-based (mais amigável)
    for index, row in df.iterrows():
        short_number = index + 1
        if only_indices is not None and short_number not in only_indices:
            continue
            
        # Verificação de Publicação
        publicado = str(row.get('Publicado', '')).strip().upper()
        if publicado == 'SIM':
            print(f"⏩ Short {short_number} já publicado. Pulando...")
            continue

        try:
            print(f"\n--- Processando Short {short_number}/{len(df)} ---")
            
            # Normaliza idioma (EN/ES/PT)
            idioma_raw = str(row['Idioma']).strip().upper()
            idioma_map = {
                'PORTUGUESE': 'PT', 'PORTUGUÊS': 'PT', 'PT-BR': 'PT', 'BRASIL': 'PT',
                'SPANISH': 'ES', 'ESPANHOL': 'ES', 'ES-ES': 'ES', 'ESPAÑOL': 'ES',
                'ENGLISH': 'EN', 'INGLES': 'EN', 'INGLÊS': 'EN', 'USA': 'EN'
            }
            idioma = idioma_map.get(idioma_raw, idioma_raw) # Fallback para o próprio valor se não mapeado (ex: 'PT', 'ES', 'EN')
            
            texto_raw = row.get('Texto', '')
            texto = str(texto_raw).strip()
            # Protege contra células vazias, NaN ou espaços
            if not texto or texto.lower() == 'nan':
                print("⚠️ Texto vazio ou inválido na coluna 'Texto'. Short será pulado.")
                continue
            img_name = row['Imagem']
            titulo = str(row['Titulo'])
            subtitulo = str(row.get('Subtitulo', '')) # Opcional
            
            # Colunas da Nova Estrutura
            # 1. Hook (0-2s)
            hook_text_raw = row.get('Hook', '')
            hook_text = str(hook_text_raw).strip() if hook_text_raw and str(hook_text_raw).lower() != 'nan' else ""
            
            # 2. Texto (Versículo) -> Já lido em 'texto'
            
            # 3. Narração Final (5-8s)
            narracao_final_raw = row.get('Narração Final', '') # Nome exato da coluna no Excel
            if not narracao_final_raw or str(narracao_final_raw).lower() == 'nan':
                 narracao_final_raw = row.get('NarracaoFinal', '') # Fallback
            narracao_final = str(narracao_final_raw).strip() if narracao_final_raw and str(narracao_final_raw).lower() != 'nan' else ""

            # 4. CTA (2-3s)
            cta_custom_raw = row.get('CTA', '')
            cta_custom = str(cta_custom_raw).strip() if cta_custom_raw and str(cta_custom_raw).lower() != 'nan' else ""
            
            # Texto específico para a Thumbnail
            palavra_thumb = str(row.get('PalavraThumb', '')).strip()
            if not palavra_thumb or palavra_thumb.lower() == 'nan':
                 palavra_thumb = titulo # Fallback se não tiver PalavraThumb

            # Marca d'água
            marca_dagua = str(row.get('MarcaDagua', '')) 
            
            # Configurações de Voz (Edge-TTS)
            voice = SHORTS_CONFIG.get(f"VOICE_{idioma}", SHORTS_CONFIG["VOICE_EN"])
            
            # Rate específico por idioma (Prompt 4)
            rate_key = f"VOICE_RATE_{idioma}"
            rate_to_use = SHORTS_CONFIG.get(rate_key, SHORTS_CONFIG.get("VOICE_RATE", "-10%"))
            
            # Definição de Estilo (Cinematic vs Viral)
            # EN/ES -> Cinematic (Frases agrupadas, Clean)
            # PT -> Viral (Palavra por palavra, Amarelo)
            is_cinematic = idioma in ['EN', 'ES']
            
            # Cor da legenda (Prompt 4)
            subtitle_color = SHORTS_CONFIG["COLOR_SUBTITLE"]

            # --- GERAÇÃO DE ÁUDIOS ---
            
            # 1. Áudio do HOOK (Novo)
            dur_hook_audio = 0.0
            timings_hook = []
            audio_path_hook = None
            if hook_text:
                audio_filename_hook = f"short_audio_hook_{index}.mp3"
                audio_path_hook = os.path.join(TEMP_AUDIO_DIR, audio_filename_hook)
                print(f"🎤 Gerando áudio do Hook...")
                timings_hook = await generate_audio_and_word_timings(hook_text, voice, audio_path_hook, rate_to_use)
                if os.path.exists(audio_path_hook):
                    dur_hook_audio = get_audio_duration(audio_path_hook)

            # 2. Áudio do VERSÍCULO (Texto Principal)
            audio_filename_main = f"short_audio_main_{index}.mp3"
            audio_path_main = os.path.join(TEMP_AUDIO_DIR, audio_filename_main)
            print(f"🎤 Gerando áudio do Versículo...")
            timings_main = await generate_audio_and_word_timings(texto, voice, audio_path_main, rate_to_use)
            
            if not timings_main:
                print("⚠️ TTS Versículo falhou nos timings. Usando estimativa.")
                timings_main = estimate_word_timings(texto, 10.0)
            
            dur_main_audio = 0.0
            if os.path.exists(audio_path_main):
                 dur_main_audio = get_audio_duration(audio_path_main)
            if dur_main_audio <= 0:
                 dur_main_audio = max(5.0, len(texto.split()) / 2.5)
                 timings_main = estimate_word_timings(texto, dur_main_audio)

            # 3. Áudio da NARRAÇÃO FINAL
            dur_outro_audio = 0.0
            timings_outro = []
            audio_path_outro = None
            if narracao_final:
                audio_filename_outro = f"short_audio_outro_{index}.mp3"
                audio_path_outro = os.path.join(TEMP_AUDIO_DIR, audio_filename_outro)
                print(f"🎤 Gerando áudio da Narração Final...")
                timings_outro = await generate_audio_and_word_timings(narracao_final, voice, audio_path_outro, rate_to_use)
                if os.path.exists(audio_path_outro):
                    dur_outro_audio = get_audio_duration(audio_path_outro)
                if not timings_outro and dur_outro_audio > 0:
                    timings_outro = estimate_word_timings(narracao_final, dur_outro_audio)
            
            # --- DEFINIÇÃO DA TIMELINE (Sequencial com Gaps) ---
            # Intro (Thumb) é um arquivo separado.
            # O vídeo principal começa com o Hook.
            
            # Durações Mínimas Visuais
            MIN_HOOK_DURATION = 2.0
            MIN_MAIN_DURATION = 10.0
            MIN_OUTRO_DURATION = 5.0
            
            GAP_DURATION = 2.0 # "Espera 2 segundos"
            CTA_DURATION = 3.0 # "CTA 3 segundos"
            
            # Calcula durações reais dos blocos de áudio
            HOOK_BLOCK_DURATION = max(MIN_HOOK_DURATION, dur_hook_audio)
            
            # Bloco de Narração (Main + Outro)
            # Vamos tratar Main e Outro como contíguos na narração, a menos que queira gap entre eles também.
            # Assumindo: Hook -> Gap(2s) -> Main -> Outro -> Gap(2s) -> CTA
            
            MAIN_BLOCK_DURATION = max(MIN_MAIN_DURATION, dur_main_audio)
            OUTRO_BLOCK_DURATION = max(MIN_OUTRO_DURATION, dur_outro_audio)
            
            # Pontos de Início na Timeline Global
            start_hook = 0.0
            end_hook = start_hook + HOOK_BLOCK_DURATION
            
            start_gap1 = end_hook
            end_gap1 = start_gap1 + GAP_DURATION
            
            start_main = end_gap1
            end_main = start_main + MAIN_BLOCK_DURATION
            
            start_outro = end_main
            end_outro = start_outro + OUTRO_BLOCK_DURATION
            
            start_gap2 = end_outro
            end_gap2 = start_gap2 + GAP_DURATION
            
            start_cta = end_gap2
            end_cta = start_cta + CTA_DURATION
            
            total_main_duration = end_cta
            
            print(f"⏱️ Timeline Detalhada (com Gaps):")
            print(f"   [{start_hook:.1f}s - {end_hook:.1f}s] HOOK (Áudio: {dur_hook_audio:.1f}s)")
            print(f"   [{start_gap1:.1f}s - {end_gap1:.1f}s] GAP 1 (2s)")
            print(f"   [{start_main:.1f}s - {end_main:.1f}s] VERSÍCULO (Áudio: {dur_main_audio:.1f}s)")
            print(f"   [{start_outro:.1f}s - {end_outro:.1f}s] NARRAÇÃO FINAL (Áudio: {dur_outro_audio:.1f}s)")
            print(f"   [{start_gap2:.1f}s - {end_gap2:.1f}s] GAP 2 (2s)")
            print(f"   [{start_cta:.1f}s - {end_cta:.1f}s] CTA (3s)")
            print(f"⏱️ Duração Total: {total_main_duration:.2f}s")

            # 3. Vídeo base (Ken Burns) com Zoom Pulsante (Prompt: Resetar atenção a cada frase)
            img_path = os.path.join(INPUT_IMAGES_SHORTS, img_name)
            if not os.path.exists(img_path):
                print(f"⚠️ Imagem {img_name} não encontrada em {INPUT_IMAGES_SHORTS}. Pulando.")
                continue

            print("🖼️ Aplicando Ken Burns Pulsante (Phrase-Based)...")
            
            # 3. Vídeo base (Ken Burns) - Zoom Suave Contínuo (User Request: "Igual ao Longo")
            print("🖼️ Aplicando Ken Burns Suave (1.0 -> 1.15) + Pan...")
            
            base_clip = apply_ken_burns_effect(
                img_path, 
                SHORTS_CONFIG["WIDTH"], 
                SHORTS_CONFIG["HEIGHT"], 
                total_main_duration,
                zoom_range=(1.0, 1.15),
                pan_range=0.03,
                force_mode='zoom_in'
            )
            
            # --- ZOOM PULSANTE REMOVIDO (User Request: Zoom Constante 1.0 -> 1.1) ---
            # O efeito base 'apply_ken_burns_effect' já aplica o zoom linear solicitado.
            # O código de pulso foi removido para evitar conflito e garantir fluidez constante.

            
            if base_clip is None: continue

            # Vinheta
            vignette = create_vignette_overlay(SHORTS_CONFIG["WIDTH"], SHORTS_CONFIG["HEIGHT"], total_main_duration)
            
            clips_to_add = []

            # --- MONTAGEM VISUAL ---
            
            # A. HOOK (Texto na tela)
            if hook_text:
                hook_img = create_text_image(
                    hook_text.upper(),
                    SHORTS_CONFIG["WIDTH"],
                    SHORTS_CONFIG["FONT_PATH_BOLD"],
                    SHORTS_CONFIG["FONT_SIZE_TITLE_MAIN"] * 1.1,
                    SHORTS_CONFIG["COLOR_TITLE"],
                    stroke_width=5,
                    stroke_fill="black",
                    line_spacing=1.1,
                    shadow=True,
                    bg_color=None # Removido fundo para limpeza visual
                )
                hook_clip = (ImageClip(hook_img)
                             .with_position(('center', 750)) # Posição Fixa Y (750px) para consistência visual entre idiomas
                             .with_start(start_hook)
                             .with_duration(HOOK_BLOCK_DURATION))
                
                try:
                    from moviepy.video.fx import FadeIn, FadeOut
                    hook_clip = hook_clip.with_effects([FadeIn(0.3), FadeOut(0.3)])
                except: pass
                
                clips_to_add.append(hook_clip)

            # B. VERSÍCULO (Legendas Unificadas - Frases Longas + Amarelo)
            # User Request: "extensa sem enter... cor amarela" -> Frases longas, amarelas, clean.
            
            # Offset para as legendas começarem no momento certo (após Gap 1)
            main_offset = start_main
            # Ajuste de Sync: -0.5s para antecipar a legenda em relação à voz
            subtitle_offset = SHORTS_CONFIG.get("SUBTITLE_OFFSET", -0.5)
            
            print(f"   [Legendas] Gerando estilo Unificado (Frases Longas, Amarelo)...")
            
            # --- ESTILO UNIFICADO (Frases Longas, Amarelo, Sem Fundo) ---
            phrases_main = []
            current_phrase = []
            
            # Agrupa palavras em frases mais longas (max 6 palavras) para evitar quebras curtas
            MAX_WORDS_PER_PHRASE = 6
            
            for item in timings_main:
                current_phrase.append(item)
                if len(current_phrase) >= MAX_WORDS_PER_PHRASE:
                    phrases_main.append(current_phrase)
                    current_phrase = []
            if current_phrase:
                phrases_main.append(current_phrase)
                
            for phrase in phrases_main:
                text_phrase = " ".join([p['word'] for p in phrase])
                start_t = phrase[0]['start'] + main_offset + subtitle_offset
                end_t = phrase[-1]['end'] + main_offset + subtitle_offset
                
                if end_t - start_t < 1.0: end_t = start_t + 1.0
                if end_t > end_main: end_t = end_main
                
                if start_t < end_main:
                    txt_img = create_text_image(
                        text_phrase,
                        SHORTS_CONFIG["WIDTH"],
                        SHORTS_CONFIG["FONT_PATH_BOLD"],
                        80, # Fonte ajustada para frases longas
                        "#FFFF00", # Amarelo (Solicitado pelo User)
                        stroke_width=3,
                        stroke_fill="black",
                        bg_color=None,
                        shadow=True,
                        shadow_offset=(4, 4),
                        shadow_fill=(0, 0, 0, 180)
                    )
                    
                    # Posição: ('center', 1150) -> Sweet Spot
                    txt_clip = (ImageClip(txt_img)
                                .with_position(('center', 1150))
                                .with_start(start_t)
                                .with_end(end_t))
                    try:
                        from moviepy.video.fx import FadeIn, FadeOut
                        # Fade suave para frases longas fica melhor
                        txt_clip = txt_clip.with_effects([FadeIn(0.2), FadeOut(0.2)])
                    except: pass
                    clips_to_add.append(txt_clip)

            # C. NARRAÇÃO FINAL (Legendas Unificadas)
            outro_offset = start_outro
            
            # --- ESTILO UNIFICADO (Frases Longas, Amarelo) ---
            phrases_outro = []
            current_phrase = []
            
            for item in timings_outro:
                current_phrase.append(item)
                if len(current_phrase) >= 6: # Max 6 palavras (consistente com Main)
                    phrases_outro.append(current_phrase)
                    current_phrase = []
            if current_phrase:
                phrases_outro.append(current_phrase)
                
            for phrase in phrases_outro:
                text_phrase = " ".join([p['word'] for p in phrase])
                start_t = phrase[0]['start'] + outro_offset + subtitle_offset
                end_t = phrase[-1]['end'] + outro_offset + subtitle_offset
                
                if end_t - start_t < 1.0: end_t = start_t + 1.0
                if end_t > end_outro: end_t = end_outro
                
                if start_t < end_outro:
                    txt_img = create_text_image(
                        text_phrase,
                        SHORTS_CONFIG["WIDTH"],
                        SHORTS_CONFIG["FONT_PATH_BOLD"],
                        80, # Fonte ajustada
                        "#FFFF00", # Amarelo
                        stroke_width=3,
                        stroke_fill="black",
                        bg_color=None,
                        shadow=True,
                        shadow_offset=(4, 4),
                        shadow_fill=(0, 0, 0, 180)
                    )
                    txt_clip = (ImageClip(txt_img)
                                .with_position(('center', 1150)) # Sweet Spot
                                .with_start(start_t)
                                .with_end(end_t))
                    try:
                        from moviepy.video.fx import FadeIn, FadeOut
                        txt_clip = txt_clip.with_effects([FadeIn(0.2), FadeOut(0.2)])
                    except: pass
                    clips_to_add.append(txt_clip)

            # D. CTA (Visual Final)
            # "Type AMEN for protection" (Ajustável por idioma)
            cta_map = {
                'PT': "DIGITE AMÉM PARA PROTEÇÃO",
                'EN': "TYPE AMEN FOR PROTECTION",
                'ES': "ESCRIBE AMÉN PARA PROTECCIÓN"
            }
            
            if cta_custom:
                cta_text_final = cta_custom
            else:
                cta_text_final = cta_map.get(idioma, "TYPE AMEN")
            
            cta_img = create_text_image(
                cta_text_final,
                SHORTS_CONFIG["WIDTH"],
                SHORTS_CONFIG["FONT_PATH_SUBSCRIBE"],
                SHORTS_CONFIG["FONT_SIZE_SUBSCRIBE"] * 0.9, # Ajuste leve se texto for longo
                "white",
                stroke_width=5,
                stroke_fill="black"
            )
            cta_clip = (ImageClip(cta_img)
                        .with_position('center')
                        .with_start(start_cta)
                        .with_duration(CTA_DURATION))

            
            # Loop Infinito: Sem FadeIn/FadeOut no final para conectar com o início
            # (Removido FadeIn para CTA se for atrapalhar o loop, mas CTA usually needs entry.
            #  O usuário pediu loop do vídeo, então o final do vídeo deve ser 'seco' ou conectar.
            #  Manter FadeIn no CTA é ok, mas o FadeOut final do vídeo/áudio deve sumir.)
            try:
                from moviepy.video.fx import FadeIn
                cta_clip = cta_clip.with_effects([FadeIn(0.5)])
            except: pass
            
            clips_to_add.append(cta_clip)
            
            # E. SUBSCRIBE (Botão + Áudio)
            # User Request: "no final... embaixo da frase final com o som tb do long"
            
            subscribe_audio_clip = None # Inicializa variável para uso posterior no mixer de áudio
            
            subscribe_text_map = {
                'PT': "INSCREVA-SE",
                'EN': "SUBSCRIBE",
                'ES': "SUSCRÍBETE"
            }
            subs_text = subscribe_text_map.get(idioma, "SUBSCRIBE")
            
            subs_img = create_text_image(
                subs_text,
                SHORTS_CONFIG["WIDTH"],
                SHORTS_CONFIG["FONT_PATH_BOLD"],
                70, 
                "#FF0000", # Vermelho YouTube
                bg_color="white", # Fundo Branco
                stroke_width=2,
                stroke_fill="black"
            )
            
            # Posição: Abaixo do CTA principal (que está no centro). 
            # Se height=1920, center=960. Vamos colocar em 1350 para dar espaço.
            subs_clip = (ImageClip(subs_img)
                         .with_position(('center', 1350))
                         .with_start(start_cta)
                         .with_duration(CTA_DURATION))
            
            try:
                from moviepy.video.fx import FadeIn
                subs_clip = subs_clip.with_effects([FadeIn(0.5)])
            except: pass
            
            clips_to_add.append(subs_clip)
            
            # Áudio do Subscribe
            subs_audio_path = os.path.join(ASSETS_DIR, "subscribe.mp3")
            if os.path.exists(subs_audio_path):
                print(f"   [Audio] Preparando efeito sonoro de Subscribe...")
                # Adiciona som sincronizado com o visual
                subscribe_audio_clip = AudioFileClip(subs_audio_path).with_start(start_cta)

            # --- ELEMENTOS DE TOPO (Título vs Salmo) ---
            
            # 1. Título (Aparece do início até antes do CTA)
            # Prompt 3: Título com fundo preto semi-transparente elegante (estilo tarja)
            title_text = titulo.upper()
            title_img = create_text_image(
                title_text,
                SHORTS_CONFIG["WIDTH"],
                SHORTS_CONFIG["FONT_PATH_BOLD"],
                45, # Um pouco maior para legibilidade
                "white",
                stroke_width=5,
                stroke_fill="black",
                bg_color=(0,0,0,160) # Mais opaco para estilo "News/Tarja"
            )
            # Vai de 0 até start_cta
            title_clip = (ImageClip(title_img)
                          .with_position(('center', 100))
                          .with_start(0)
                          .with_end(start_cta))
            clips_to_add.append(title_clip)
            
            # 2. Salmo/Subtitulo (Volta no CTA)
            # "salmo so voltar no cta"
            if subtitulo and subtitulo.lower() != 'nan':
                salmo_text = subtitulo
                salmo_img = create_text_image(
                    salmo_text,
                    SHORTS_CONFIG["WIDTH"],
                    SHORTS_CONFIG["FONT_PATH_BOLD"],
                    50, # Um pouco maior para destaque final
                    "#FFD700", # Dourado
                    stroke_width=2,
                    stroke_fill="black",
                    bg_color=(0,0,0,80)
                )
                salmo_clip = (ImageClip(salmo_img)
                              .with_position(('center', 100)) # Mesma posição do título
                              .with_start(start_cta)
                              .with_duration(CTA_DURATION))
                clips_to_add.append(salmo_clip)
            
            # Marca d'água
            if marca_dagua:
                wm_img = create_text_image(marca_dagua, SHORTS_CONFIG["WIDTH"], SHORTS_CONFIG["FONT_PATH"], 30, "white", stroke_width=2)
                wm_clip = ImageClip(wm_img).with_position(('center', 1750)).with_opacity(0.7).with_duration(total_main_duration)
                clips_to_add.append(wm_clip)

            # MONTAGEM FINAL DO VÍDEO PRINCIPAL
            main_video_clip = CompositeVideoClip([base_clip.with_position('center'), vignette] + clips_to_add, size=(SHORTS_CONFIG["WIDTH"], SHORTS_CONFIG["HEIGHT"]))
            
            # MONTAGEM DO ÁUDIO COMPLETO
            final_audio_tracks = []
            
            # 1. Hook Audio
            if audio_path_hook and os.path.exists(audio_path_hook):
                hook_audio_clip = AudioFileClip(audio_path_hook).with_start(start_hook)
                final_audio_tracks.append(hook_audio_clip)
 
            # 2. Main Audio (Versículo) - Inicia após Gap 1
            if os.path.exists(audio_path_main):
                main_audio_clip = AudioFileClip(audio_path_main).with_start(start_main)
                final_audio_tracks.append(main_audio_clip)
            
            # 3. Outro Audio (Final) - Inicia logo após Main (sem gap extra entre eles, mas gap depois)
            if audio_path_outro and os.path.exists(audio_path_outro):
                outro_audio_clip = AudioFileClip(audio_path_outro).with_start(start_outro)
                final_audio_tracks.append(outro_audio_clip)
                
            # 4. Música de fundo (Trilha Principal)
            bg_music_path = os.path.join(ASSETS_DIR, "Pulsar - The Grey Room _ Density & Time.mp3")
            if os.path.exists(bg_music_path):
                bg_music = AudioFileClip(bg_music_path)
                # Loop infinito para cobrir tudo
                bg_music = concatenate_audioclips([bg_music] * (int(total_main_duration // bg_music.duration) + 1))
                bg_music = bg_music.with_duration(total_main_duration)
                
                # Volume da Música: Mantém audível mas suave (-18dB ~ 0.12)
                bg_music = bg_music.with_volume_scaled(0.12)
                
                final_audio_tracks.append(bg_music)
            
            # 5. Audio Layering: Ambiente (Natureza) - Request: "sob a trilha sonora principal" (-25dB)
            nature_file = None
            # Tenta encontrar arquivo de natureza
            for f in os.listdir(ASSETS_DIR):
                if "nature" in f.lower() or "wind" in f.lower() or "forest" in f.lower():
                    nature_file = os.path.join(ASSETS_DIR, f)
                    break
            
            if nature_file:
                print(f"   [Audio] Adicionando camada de Natureza: {os.path.basename(nature_file)}")
                nature_clip = AudioFileClip(nature_file)
                loops_nat = int(total_main_duration / nature_clip.duration) + 1
                nature_clip = concatenate_audioclips([nature_clip] * loops_nat).with_duration(total_main_duration)
                
                # Volume -25dB (~0.06)
                nature_clip = nature_clip.with_volume_scaled(0.06)
                final_audio_tracks.append(nature_clip)
            else:
                print("   [Audio] Nenhum arquivo de natureza encontrado em assets (nature/wind/forest).")


            
            # 6. Subscribe Audio (Efeito)
            if subscribe_audio_clip:
                final_audio_tracks.append(subscribe_audio_clip)

            if final_audio_tracks:
                main_video_clip = main_video_clip.with_audio(CompositeAudioClip(final_audio_tracks))
            
            # --- GERAÇÃO DE THUMBNAIL (INTRO CLIP) ---
            img_name_no_ext = os.path.splitext(os.path.basename(img_path))[0]
            safe_title = "".join([c for c in titulo if c.isalnum() or c in (' ', '_')]).strip().replace(" ", "_")
            out_filename = f"{idioma}_{img_name_no_ext}_{safe_title}.mp4"
            out_path = os.path.join(OUTPUT_SHORTS, out_filename)
            thumb_path = out_path.replace(".mp4", "_thumb.jpg") 

            print("🖼️ Gerando Thumbnail (Intro)...")
            
            top_content = subtitulo if subtitulo and subtitulo.lower() != 'nan' else titulo
            
            create_thumbnail(
                img_path, 
                palavra_thumb.upper(), 
                thumb_path, 
                SHORTS_CONFIG["WIDTH"], 
                SHORTS_CONFIG["HEIGHT"], 
                SHORTS_CONFIG["FONT_PATH_BOLD"],
                top_text=top_content,      
                main_text=palavra_thumb.upper() 
            )

            # --- 3. Cria intro usando a thumbnail como primeiro quadro ---
            intro_duration = SHORTS_CONFIG.get("THUMB_INTRO_DURATION", 2.0)
            intro_clip = ImageClip(thumb_path).with_duration(intro_duration)

            try:
                def _intro_scale(t):
                    max_zoom = 1.08
                    if intro_duration <= 0:
                        return 1.0
                    ramp = t / 0.3
                    if ramp > 1.0:
                        ramp = 1.0
                    return 1.0 + (max_zoom - 1.0) * ramp

                intro_clip = intro_clip.resize(_intro_scale)
            except Exception:
                pass
            
            # Transição suave (Fade Out na intro e Fade In no vídeo principal)
            try:
                from moviepy.video.fx import FadeOut, FadeIn
                
                # Intro desaparece suavemente (1.0s)
                intro_clip = intro_clip.with_effects([FadeOut(1.0)])
                
                # Vídeo principal aparece suavemente (1.0s)
                main_video_clip = main_video_clip.with_effects([FadeIn(1.0)])
                
            except ImportError:
                pass

            # --- 4. Concatena (INTRO + VÍDEO) em um único clipe final ---
            # O áudio já foi composto no main_video_clip, então não precisamos refazer a música de fundo aqui.
            # Apenas garantimos que a intro tenha o mesmo áudio se necessário, ou silêncio.
            # Na lógica anterior, a intro era muda ou tinha seu próprio efeito.
            
            # Ajuste de Fade na Intro para transição suave
            try:
                from moviepy.video.fx import FadeOut, FadeIn
                intro_clip = intro_clip.with_effects([FadeOut(0.5)])
                main_video_clip = main_video_clip.with_effects([FadeIn(0.5)])
            except: pass

            final_video = concatenate_videoclips([intro_clip, main_video_clip])
            
            print(f"💾 Salvando vídeo em: {out_path}")
            final_video.write_videofile(out_path, fps=SHORTS_CONFIG["FPS"], codec='libx264', audio_codec='aac')
            
        except Exception as e:
            print(f"❌ Erro ao processar linha {index}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    from scripts import validate_roteiro
    from scripts.verificar_falhas import verificar_falhas

    try:
        validate_roteiro.main()
    except SystemExit as e:
        if e.code != 0:
            print("❌ Validação da planilha falhou. Corrija os erros antes de gerar os Shorts.")
            sys.exit(e.code)

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

    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "ultimo_log.txt")
    sys.stdout = DualLogger(log_file)

    print("=== INÍCIO DA RODADA DE GERAÇÃO DE SHORTS ===\n")

    target_shorts = None
    args = sys.argv[1:]
    if args:
        indices = []
        for a in args:
            try:
                indices.append(int(a))
            except ValueError:
                print(f"⚠️ Argumento ignorado (não é número de Short): {a}")
        if indices:
            target_shorts = set(indices)
            print(f"🔁 Gerando apenas os Shorts: {sorted(target_shorts)}")

    asyncio.run(process_shorts_from_excel(target_shorts))

    falhos = verificar_falhas()
    if falhos:
        print(f"🔁 Reprocessando automaticamente Shorts com falha de áudio/TTS: {sorted(falhos)}")
        asyncio.run(process_shorts_from_excel(set(falhos)))

    print("\n=== FIM DA RODADA DE GERAÇÃO DE SHORTS ===")
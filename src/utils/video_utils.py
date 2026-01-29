import os
import random
import textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy import VideoClip, ImageClip

# Tenta importar ImageResampling (Pillow 10+) ou usa fallback
try:
    from PIL.Image import Resampling
    LANCZOS = Resampling.LANCZOS
except ImportError:
    from PIL.Image import LANCZOS

def create_text_image(text, width, font_path, font_size, color, bg_color=None, align='center', stroke_width=5, stroke_fill='black', line_spacing=1.5, shadow=True, shadow_offset=(2, 2), shadow_fill=(0, 0, 0, 178)):
    """
    Cria uma imagem PIL com o texto desenhado.
    Suporta realce de texto com asteriscos (ex: *PALAVRA* fica Amarela).
    """
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        font = ImageFont.load_default()
        print(f"AVISO: Fonte {font_path} não encontrada, usando padrão.")

    avg_char_width = font.getlength("x")
    
    # Padding lateral de 15% (Prompt 1)
    safe_width = int(width * 0.70) 
    
    # Preserva asteriscos no wrap
    max_chars = int(safe_width / avg_char_width) if avg_char_width > 0 else len(text)
    lines = textwrap.wrap(text, width=max_chars)
    
    if len(lines) > 1 and len(lines[-1]) < 4: 
         lines = textwrap.wrap(text, width=int(max_chars * 0.7))
    
    if len(lines) == 2:
        l1 = lines[0]
        l2 = lines[1]
        if len(l1) > len(l2) * 2:
             balanced_lines = textwrap.wrap(text, width=int(max_chars * 0.6))
             if len(balanced_lines) <= 2:
                 lines = balanced_lines

    bbox = font.getbbox("hg")
    line_height = int(bbox[3] * line_spacing)
    img_height = line_height * len(lines) + 20
    
    # Cria imagem transparente
    img = Image.new('RGBA', (width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Desenha Fundo (Box) semi-transparente
    if bg_color:
        max_line_w = 0
        for line in lines:
            # Remove asteriscos para calcular largura real
            clean_line = line.replace('*', '')
            w = font.getlength(clean_line)
            if w > max_line_w: max_line_w = w
            
        padding = 20
        box_w = max_line_w + (padding * 4)
        box_h = img_height - 5
        
        box_x = (width - box_w) / 2
        box_y = 5
        
        draw.rounded_rectangle(
            [box_x, box_y, box_x + box_w, box_y + box_h], 
            radius=20, 
            fill=bg_color
        )

    y_text = 10
    highlight_state = False # False = Normal, True = Highlight (#FFD700)
    
    # Pré-processamento das linhas para renderização
    for i_line, line in enumerate(lines):
        parts = line.split('*')
        clean_line = "".join(parts)
        line_w = font.getlength(clean_line)
        x = (width - line_w) / 2
        
        # Segmentos da linha
        segments = []
        curr_x = x
        
        for i, part in enumerate(parts):
            if i > 0: highlight_state = not highlight_state
            if not part: continue
            
            seg_color = "#FFD700" if highlight_state else color
            seg_w = font.getlength(part)
            
            segments.append({
                'text': part,
                'x': curr_x,
                'y': y_text,
                'color': seg_color,
                'width': seg_w
            })
            curr_x += seg_w
            
        # 1. Sombra (Shadow)
        if shadow:
            shadow_layer = Image.new('RGBA', (width, img_height), (0,0,0,0))
            shadow_draw = ImageDraw.Draw(shadow_layer)
            sx, sy = shadow_offset
            
            for seg in segments:
                shadow_draw.text((seg['x'] + sx, seg['y'] + sy), seg['text'], font=font, fill=shadow_fill)
                
            # Aplica Blur na sombra
            shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=3))
            img.paste(shadow_layer, (0,0), shadow_layer)

        # 2. Stroke (Contorno)
        if stroke_width > 0:
            for seg in segments:
                for adj_x in range(-stroke_width, stroke_width + 1):
                    for adj_y in range(-stroke_width, stroke_width + 1):
                        draw.text((seg['x'] + adj_x, seg['y'] + adj_y), seg['text'], font=font, fill=stroke_fill)
        
        # 3. Fill (Texto Colorido)
        for seg in segments:
            draw.text((seg['x'], seg['y']), seg['text'], font=font, fill=seg['color'])
            
        y_text += line_height
        
    return np.array(img)

def create_vignette_overlay(width, height, duration, top_opacity=0.6, bottom_opacity=0.7):
    """
    Cria uma sombra (degradê) preta na parte inferior e superior.
    """
    gradient = np.zeros((height, width, 4), dtype=np.uint8)
    
    top_limit = int(height * 0.15)
    bottom_limit = int(height * 0.75)
    
    for y in range(height):
        alpha = 0
        if y < top_limit:
            # Topo escurecendo
            alpha = int(255 * top_opacity * (1 - y/top_limit))
        elif y > bottom_limit:
            # Fundo escurecendo
            alpha = int(255 * bottom_opacity * ((y - bottom_limit) / (height - bottom_limit)))
            
        if alpha > 0:
            gradient[y, :, 3] = alpha # A
            
    img = Image.fromarray(gradient)
    return ImageClip(np.array(img)).with_duration(duration)

def apply_ken_burns_effect(image_path, width, height, duration, zoom_speed=0.03, pan_speed=1, zoom_range=None, pan_range=None, force_mode=None):
    """
    Gera o clipe com variação de movimento (Zoom OU Pan) SUAVE.
    Parâmetros Opcionais:
    - zoom_range: tupla (start, end) ex: (1.0, 1.1)
    - pan_range: float (ex: 0.03 para 3%) ou tupla (start, end)
    - force_mode: 'zoom_in', 'zoom_out', 'pan_right', 'pan_left'
    """
    try:
        original_img = Image.open(image_path).convert('RGB')
    except Exception as e:
        print(f"Erro ao abrir imagem {image_path}: {e}")
        return None
    
    # Decisão de Modo (Variação de Movimento) - Determinístico por Imagem
    if force_mode:
        mode = force_mode
    else:
        import hashlib
        img_hash = int(hashlib.md5(image_path.encode('utf-8')).hexdigest(), 16)
        modes = ['zoom_in', 'zoom_out', 'pan_right', 'pan_left']
        mode = modes[img_hash % len(modes)]
        # Se duração muito curta, Zoom In é mais seguro
        if duration < 3.0: mode = 'zoom_in'

    # 1. Prepara a imagem base
    target_ratio = width / height
    img_ratio = original_img.width / original_img.height
    
    # Determina tamanho base (que cobre a tela 100%)
    if img_ratio > target_ratio:
        base_h = height
        base_w = int(base_h * img_ratio)
    else:
        base_w = width
        base_h = int(base_w / img_ratio)
        
    # --- Lógica de Zoom/Pan ---
    
    # Defaults baseados em zoom_speed se ranges não forem passados
    max_zoom_intensity = min(zoom_speed * duration, 0.10)
    if max_zoom_intensity < 0.03: max_zoom_intensity = 0.03
    
    s_start, s_end = 1.0, 1.0
    pan_x_start, pan_x_end = 0.0, 0.0
    
    if zoom_range:
        s_start, s_end = zoom_range
    else:
        if mode == 'zoom_in':
            s_start, s_end = 1.0, 1.0 + max_zoom_intensity
        elif mode == 'zoom_out':
            s_start, s_end = 1.0 + max_zoom_intensity, 1.0
        elif 'pan' in mode:
             s_start, s_end = 1.10, 1.10 # Pan precisa de zoom fixo
    
    if pan_range is not None:
        # Se pan_range for um único float, tratamos como intensidade
        if isinstance(pan_range, (int, float)):
             direction = 1 if mode == 'pan_right' else -1
             pan_x_start = -pan_range * direction
             pan_x_end = pan_range * direction
        else:
             pan_x_start, pan_x_end = pan_range
    else:
        if 'pan' in mode:
             direction = 1 if mode == 'pan_right' else -1
             pan_x_start = -0.05 * direction # 5% default
             pan_x_end = 0.05 * direction

    # Tamanho máximo necessário para o redimensionamento inicial
    max_scale_needed = max(s_start, s_end)
    max_w = int(base_w * max_scale_needed)
    max_h = int(base_h * max_scale_needed)
    
    # Usa a imagem original para resize de alta qualidade
    # Redimensiona para o tamanho MÁXIMO necessário de uma vez
    pil_img_resized = original_img.resize((max_w, max_h), Image.LANCZOS)
    img_np = np.array(pil_img_resized)
    
    def make_frame(t):
        progress = t / duration
        
        # Interpolação Linear
        current_scale = s_start + (s_end - s_start) * progress
        
        # Fator de Pan (0.0 a 1.0 relativo ao excesso)
        current_pan = pan_x_start + (pan_x_end - pan_x_start) * progress
        
        # Calculando o Crop na imagem img_np:
        # img_np W = base_w * max_scale_needed
        # Queremos mostrar uma janela que representa 'width' na escala 'current_scale'.
        # Janela W = width * (max_scale_needed / current_scale)
        # Janela H = height * (max_scale_needed / current_scale)
        
        crop_w = int(width * (max_scale_needed / current_scale))
        crop_h = int(height * (max_scale_needed / current_scale))
        
        # Centralizar
        center_x = max_w / 2
        center_y = max_h / 2
        
        # Aplicar Pan (Deslocamento do centro)
        # current_pan é deslocamento em % da largura base?
        offset_x = base_w * current_pan
        
        x1 = int(center_x + offset_x - crop_w / 2)
        y1 = int(center_y - crop_h / 2)
        
        # Clamp
        x1 = max(0, min(x1, max_w - crop_w))
        y1 = max(0, min(y1, max_h - crop_h))
        
        # Crop
        crop = img_np[y1:y1+crop_h, x1:x1+crop_w]
        
        # Resize final para (width, height) - necessário pois o crop muda de tamanho
        # OpenCV é mais rápido que PIL para isso
        import cv2
        frame = cv2.resize(crop, (width, height), interpolation=cv2.INTER_LINEAR)
        return frame

    return VideoClip(make_frame, duration=duration)

def create_thumbnail(image_path, title, output_path, width, height, font_path, watermark=None, subtitle=None, top_text=None, main_text=None):
    """
    Cria uma thumbnail vertical (9:16) com alto impacto.
    
    Parâmetros:
    - top_text: Texto secundário (ex: "Salmo 23") que ficará no TOPO com box de destaque.
    - main_text: Palavra-chave GIGANTE (ex: "HOPE") que ficará na parte inferior.
    (Se main_text não for passado, usa 'title' como fallback).
    """
    try:
        with Image.open(image_path) as img:
            img = img.convert("RGBA")
        
        # --- ESTRATÉGIA PARA VÍDEOS LONGOS (LANDSCAPE) - SPLIT SCREEN ---
        is_landscape = width > height
        
        if is_landscape:
            # === LAYOUT "SPLIT SCREEN" (MEIO A MEIO) ===
            # Lado Esquerdo: Texto sobre fundo escuro
            # Lado Direito: Imagem do personagem
            
            # 1. Background (Dark Blue/Black)
            bg_color = (15, 15, 20) 
            img_final = Image.new('RGB', (width, height), bg_color)
            
            # 2. Imagem (Lado Direito)
            # Redimensiona para caber na altura
            ratio = height / img.height
            new_w = int(img.width * ratio)
            new_h = height
            resized = img.resize((new_w, new_h), LANCZOS)
            
            # Posição de corte (Split)
            # A imagem começa em 40% da tela, dando 60% para ela (ou vice-versa)
            split_x = int(width * 0.40) 
            
            # Cola a imagem alinhada à direita
            paste_x = width - new_w
            if paste_x < split_x: paste_x = split_x
            
            # Se a imagem for mais larga que o espaço disponível, corta a esquerda
            available_w = width - split_x
            if new_w > available_w:
                crop_left = (new_w - available_w) // 2
                resized = resized.crop((crop_left, 0, crop_left + available_w, height))
                paste_x = split_x
            
            img_final.paste(resized, (paste_x, 0))
            
            # 3. Blending (Degradê na emenda)
            grad_w = 400
            overlay = Image.new('RGBA', (grad_w, height), (0,0,0,0))
            draw_ov = ImageDraw.Draw(overlay)
            
            for x in range(grad_w):
                # Alpha vai de 255 (Cor do fundo) até 0 (Transparente)
                alpha = int(255 * (1 - (x / grad_w)))
                draw_ov.line([(x, 0), (x, height)], fill=(bg_color[0], bg_color[1], bg_color[2], alpha))
            
            # Cola o degradê sobre a borda esquerda da imagem
            img_final.paste(overlay, (paste_x - 100, 0), overlay)
            
            draw = ImageDraw.Draw(img_final)
            
            # 4. Texto (Lado Esquerdo)
            text_area_w = split_x + 50
            center_x = text_area_w // 2
            
            # Top Text (Dourado)
            texto_topo = top_text if top_text else (watermark if watermark else subtitle)
            if texto_topo:
                try: t_font = ImageFont.truetype(font_path, 48)
                except: t_font = ImageFont.load_default()
                bbox = t_font.getbbox(texto_topo)
                tw = bbox[2] - bbox[0]
                draw.text((center_x - tw//2, 80), texto_topo, font=t_font, fill="#FFD700")
            
            # Main Text (Branco Gigante)
            texto_gigante = main_text if main_text else title
            if not texto_gigante: texto_gigante = "VIDEO"
            
            f_size = 150
            found_font = None
            final_lines = []
            
            while f_size > 60:
                try: f = ImageFont.truetype(font_path, f_size)
                except: f = ImageFont.load_default(); break
                
                avg_char = f.getlength("A")
                chars = int((text_area_w - 60) / avg_char)
                lines = textwrap.wrap(texto_gigante, width=chars)
                
                max_w = 0
                for l in lines:
                    if f.getlength(l) > max_w: max_w = f.getlength(l)
                
                if max_w < (text_area_w - 40):
                    found_font = f
                    final_lines = lines
                    break
                f_size -= 10
            
            if not found_font:
                found_font = ImageFont.load_default()
                final_lines = [texto_gigante]
            
            line_h = int(found_font.getbbox("Ay")[3] * 1.1)
            total_h = line_h * len(final_lines)
            start_y = (height - total_h) // 2
            
            curr_y = start_y
            for line in final_lines:
                lw = found_font.getlength(line)
                draw.text((center_x - lw//2, curr_y), line, font=found_font, fill="#FFD700")
                curr_y += line_h
                
            img_final.convert("RGB").save(output_path, quality=100)
            return

        # --- ESTRATÉGIA PARA SHORTS (PORTRAIT) ---
        # 1. Redimensionamento e Crop (Preencher 9:16)
        img_ratio = img.width / img.height
        target_ratio = width / height
        
        if img_ratio > target_ratio:
            new_height = height
            new_width = int(new_height * img_ratio)
            img = img.resize((new_width, new_height), LANCZOS)
            left = (new_width - width) // 2
            img = img.crop((left, 0, left + width, height))
        else:
            new_width = width
            new_height = int(new_width / img_ratio)
            img = img.resize((new_width, new_height), LANCZOS)
            top = (new_height - height) // 2
            img = img.crop((0, top, width, top + height))
        
        draw = ImageDraw.Draw(img)

        # --- 2. Topo: Box "Sticker" para o Salmo (top_text) ---
        # Se top_text não vier, tenta usar watermark ou subtitle como fallback
        texto_topo = top_text if top_text else (watermark if watermark else subtitle)
        
        if texto_topo:
            try:
                # Fonte do topo (menor, mas legível)
                top_font_size = 42
                top_font = ImageFont.truetype(font_path, top_font_size)
            except:
                top_font = ImageFont.load_default()
            
            # Mede o texto
            bbox = top_font.getbbox(texto_topo)
            txt_w = bbox[2] - bbox[0]
            txt_h = bbox[3] - bbox[1]
            
            # Padding do box
            pad_x = 30
            pad_y = 15
            
            box_w = txt_w + (pad_x * 2)
            box_h = txt_h + (pad_y * 2)
            
            # Desenha Box Arredondado
            if is_landscape:
                # --- ESTILO LONGOS (CINEMÁTICO) ---
                # Sem box, apenas texto branco com sombra forte para visual limpo
                
                text_x = (width - txt_w) // 2
                text_y = 60
                
                # Shadow
                shadow_offset = 3
                draw.text((text_x + shadow_offset, text_y + shadow_offset), texto_topo, font=top_font, fill="black")
                draw.text((text_x - shadow_offset, text_y + shadow_offset), texto_topo, font=top_font, fill="black")
                draw.text((text_x + shadow_offset, text_y - shadow_offset), texto_topo, font=top_font, fill="black")
                draw.text((text_x - shadow_offset, text_y - shadow_offset), texto_topo, font=top_font, fill="black")
                
                draw.text((text_x, text_y), texto_topo, font=top_font, fill="white")
            
            else:
                # --- ESTILO SHORTS (STICKER) ---
                # Mantém o estilo original de "Selo" que o usuário já aprovou para Shorts
                
                # Posição: Centralizado no topo (com margem de 60px)
                box_x = (width - box_w) // 2
                box_y = 60 
                
                # Desenha Box Arredondado (Amarelo Claro / Creme)
                box_color = "#FFF2CC" 
                draw.rounded_rectangle(
                    [box_x, box_y, box_x + box_w, box_y + box_h],
                    radius=15,
                    fill=box_color,
                    outline="black",
                    width=2
                )
                
                # Desenha o Texto (Preto)
                text_x = box_x + pad_x
                text_y = box_y + pad_y - 4
                draw.text((text_x, text_y), texto_topo, font=top_font, fill="black")


        # --- 3. Base: Palavra GIGANTE (main_text) ---
        # Usa main_text se existir, senão usa title
        texto_gigante = main_text if main_text else title
        if not texto_gigante: texto_gigante = "SHORTS" # Fallback extremo
        texto_gigante = texto_gigante.upper() # Prompt 1: Uppercase Obrigatório

        # Tamanho: Começa AINDA MAIOR (210px) como pedido
        font_size = 210
        min_font_size = 50 
        
        # Stroke Ajustado
        stroke_thickness = 10
        
        final_font = None
        final_lines = []
        
        # Padding lateral de 15% (Prompt 1)
        safe_width = int(width * 0.70)

        # Loop para encontrar tamanho que caiba na largura segura
        current_size = font_size
        while current_size >= min_font_size:
            try:
                f = ImageFont.truetype(font_path, current_size)
            except:
                f = ImageFont.load_default(); break
            
            # --- NOVA LÓGICA DE QUEBRA ---
            
            # 1. Tenta LINHA ÚNICA primeiro
            w_full = f.getlength(texto_gigante)
            if w_full <= safe_width:
                final_font = f
                final_lines = [texto_gigante]
                break
            
            # 2. Se não coube em uma linha...
            if " " not in texto_gigante:
                current_size -= 5
                continue

            # 3. Se tem espaços, tenta quebrar
            avg_char = f.getlength("A")
            chars = int(safe_width / avg_char)
            lines = textwrap.wrap(texto_gigante, width=chars)
            
            max_w = 0
            for l in lines:
                if f.getlength(l) > max_w: max_w = f.getlength(l)
            
            if max_w <= safe_width:
                final_font = f
                final_lines = lines
                break
                
            current_size -= 10
        
        if not final_font:
            final_font = ImageFont.load_default()
            final_lines = [texto_gigante]
        
        # Calcula altura total do bloco de texto
        line_h = int(final_font.getbbox("Ay")[3] * 1.1)
        total_h = line_h * len(final_lines)
        
        # Posiciona na parte inferior (Bottom 15% margin)
        start_y = height - total_h - 250 
        
        # Desenha Sombra com Blur (Prompt 1)
        shadow_layer = Image.new('RGBA', (width, height), (0,0,0,0))
        shadow_draw = ImageDraw.Draw(shadow_layer)
        sx, sy = 15, 15 # Offset aumentado para efeito 3D Intenso (Prompt 3)
        
        curr_y = start_y
        for line in final_lines:
            lw = final_font.getlength(line)
            lx = (width - lw) // 2
            
            # Desenha na camada de sombra (Escura e Intensa: 200 de opacidade)
            shadow_draw.text((lx + sx, curr_y + sy), line, font=final_font, fill=(0,0,0,200))
            curr_y += line_h
            
        # Aplica Blur na sombra (Radius 15 para "blur intenso")
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=15))
        img.paste(shadow_layer, (0,0), shadow_layer)
        
        # Desenha Texto Principal (Branco com Stroke Preto)
        curr_y = start_y
        for line in final_lines:
            lw = final_font.getlength(line)
            lx = (width - lw) // 2
            
            # Stroke
            for adj_x in range(-stroke_thickness, stroke_thickness+1):
                for adj_y in range(-stroke_thickness, stroke_thickness+1):
                     draw.text((lx+adj_x, curr_y+adj_y), line, font=final_font, fill="black")
            
            # Fill
            draw.text((lx, curr_y), line, font=final_font, fill="#FFD700")
            curr_y += line_h

        img.convert("RGB").save(output_path, quality=100)
        return True
        
    except Exception as e:
        print(f"Erro ao criar thumbnail: {e}")
        import traceback
        traceback.print_exc()
        return False


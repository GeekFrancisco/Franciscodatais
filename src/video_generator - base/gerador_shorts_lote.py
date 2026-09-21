import os
import numpy as np
from PIL import Image
from moviepy import VideoClip

# --- CONFIGURAÇÕES GERAIS ---
CONFIG = {
    "WIDTH": 1080,
    "HEIGHT": 1920,
    "DEFAULT_DURATION": 15,  # Duração padrão se não houver áudio (segundos)
    "FPS": 30,
    "ZOOM_SPEED": 0.03,      # 3% de zoom por segundo (Muito suave)
    "PAN_SPEED": 3           # 3 pixels por segundo (Quase imperceptível, apenas para dar vida)
}

def apply_ken_burns_effect(clip, image_path, duration):
    """
    Aplica efeito Ken Burns (Zoom + Pan suave) otimizado para Shorts.
    """
    # Carrega imagem uma vez
    original_img = Image.open(image_path).convert('RGB')
    
    # Redimensiona para cobrir a tela (preenche 1080x1920 mantendo proporção)
    # Isso garante que não haja bordas pretas iniciais
    target_ratio = CONFIG["WIDTH"] / CONFIG["HEIGHT"]
    img_ratio = original_img.width / original_img.height
    
    if img_ratio > target_ratio:
        # Imagem mais larga que a tela: ajusta pela altura
        base_h = CONFIG["HEIGHT"]
        base_w = int(base_h * img_ratio)
    else:
        # Imagem mais alta ou igual: ajusta pela largura
        base_w = CONFIG["WIDTH"]
        base_h = int(base_w / img_ratio)
        
    original_resized = original_img.resize((base_w, base_h), Image.LANCZOS)
    
    def make_frame(t):
        # 1. CÁLCULO DO ZOOM
        # Scale começa em 1.0 e aumenta lentamente
        scale = 1 + (CONFIG["ZOOM_SPEED"] * t)
        
        current_w = int(base_w * scale)
        current_h = int(base_h * scale)
        
        # Redimensionamento dinâmico
        # Mudamos para LANCZOS para evitar tremor/aliasing, mesmo sendo mais lento
        img = original_resized.resize((current_w, current_h), Image.LANCZOS)
        
        # 2. CÁLCULO DO PAN (Movimento Lateral/Vertical)
        # O zoom cria uma "sobra" de imagem que podemos explorar para o Pan
        max_offset_x = current_w - CONFIG["WIDTH"]
        max_offset_y = current_h - CONFIG["HEIGHT"]
        
        # Centraliza inicialmente
        # Usamos round() para arredondamento mais estável que int() simples
        center_x = max_offset_x / 2
        center_y = max_offset_y / 2
        
        # Adiciona deslocamento linear suave
        pan_offset = CONFIG["PAN_SPEED"] * t
        
        # Aplica o offset
        pos_x = int(round(center_x + pan_offset))
        pos_y = int(round(center_y + pan_offset))
        
        # 3. SEGURANÇA (Clamping)
        # Garante que o corte nunca saia dos limites da imagem
        if pos_x < 0: pos_x = 0
        if pos_x > max_offset_x: pos_x = max_offset_x
        if pos_y < 0: pos_y = 0
        if pos_y > max_offset_y: pos_y = max_offset_y
        
        # 4. CORTE FINAL (Crop 1080x1920)
        return np.array(img.crop((pos_x, pos_y, pos_x + CONFIG["WIDTH"], pos_y + CONFIG["HEIGHT"])))

    return VideoClip(make_frame, duration=duration)

def processar_lote():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_folder = os.path.join(base_dir, "input_images")
    output_folder = os.path.join(base_dir, "output_videos")
    
    os.makedirs(output_folder, exist_ok=True)
    
    # Lista todas as imagens
    images = [f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    
    if not images:
        print("Nenhuma imagem encontrada em input_images!")
        return

    print(f"Encontradas {len(images)} imagens. Iniciando processamento em lote...")
    print(f"Configuração: {CONFIG['WIDTH']}x{CONFIG['HEIGHT']} | {CONFIG['FPS']} FPS")

    for idx, img_name in enumerate(images):
        print(f"\n[{idx+1}/{len(images)}] Processando: {img_name}")
        
        input_path = os.path.join(input_folder, img_name)
        output_path = os.path.join(output_folder, f"Short_{os.path.splitext(img_name)[0]}.mp4")
        
        # Aqui futuramente leremos a duração do áudio. Por enquanto usa padrão.
        duration = CONFIG["DEFAULT_DURATION"]
        
        try:
            # Gera o vídeo
            clip = apply_ken_burns_effect(None, input_path, duration)
            
            # Salva
            clip.with_fps(CONFIG["FPS"]).write_videofile(
                output_path, 
                codec='libx264', 
                audio=False, 
                preset='ultrafast', # Use 'medium' para qualidade final melhor
                threads=4
            )
            print(f"Sucesso: {output_path}")
            
        except Exception as e:
            print(f"Erro ao processar {img_name}: {e}")

if __name__ == "__main__":
    processar_lote()
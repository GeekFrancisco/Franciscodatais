import os
import numpy as np
from PIL import Image, ImageDraw
# Tenta importar do moviepy (compatibilidade v1 e v2)
try:
    # Tenta importação antiga (v1.x)
    from moviepy.editor import ImageClip, CompositeVideoClip
except ImportError:
    try:
        # Tenta importação nova (v2.x)
        from moviepy import ImageClip, CompositeVideoClip
        # Se precisar de submodulos específicos na v2, ajustaremos aqui
    except ImportError as e:
        print(f"Erro detalhado ao importar moviepy: {e}")
        print("Tente rodar: pip install moviepy")
        exit()

def create_test_image(path):
    """Cria uma imagem de teste colorida se não existir nenhuma."""
    print("Criando imagem de teste...")
    # Cria imagem 1080x1920 (formato Shorts)
    img = Image.new('RGB', (1080, 1920), color = (73, 109, 137))
    d = ImageDraw.Draw(img)
    
    # Desenha um texto no centro
    text = "TESTE DE ZOOM"
    # Tenta centralizar mais ou menos (cálculo simples)
    d.text((400, 900), text, fill=(255, 255, 0))
    
    img.save(path)
    print(f"Imagem criada em: {path}")

def zoom_in_effect(clip, image_path, zoom_ratio=0.1):
    """Aplica um efeito de zoom in progressivo no clipe."""
    
    # MoviePy 2.0: Usar VideoClip com make_frame EXPLICITO
    from moviepy import VideoClip

    # Carrega a imagem original como um array numpy UMA VEZ
    original_img = Image.open(image_path).convert('RGB')
    base_w, base_h = original_img.size
    
    def make_frame(t):
        # Zoom progressivo
        scale = 1 + (zoom_ratio * t) 
        
        # Calcula novo tamanho
        new_w = int(base_w * scale)
        new_h = int(base_h * scale)
        
        # Redimensiona usando PIL
        img_resized = original_img.resize((new_w, new_h), Image.BILINEAR)
        
        # Calcula o corte central
        left = (new_w - base_w) // 2
        top = (new_h - base_h) // 2
        right = left + base_w
        bottom = top + base_h
        
        # Corta
        img_cropped = img_resized.crop((left, top, right, bottom))
        
        return np.array(img_cropped)

    # Cria o clipe de vídeo
    return VideoClip(make_frame, duration=clip.duration)

def processar_video():
    # Caminhos relativos ao local do script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_folder = os.path.join(base_dir, "input_images")
    output_folder = os.path.join(base_dir, "output_videos")
    
    # Garante que as pastas existem
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)
    
    # Busca imagens
    valid_extensions = ('.jpg', '.png', '.jpeg')
    images = [f for f in os.listdir(input_folder) if f.lower().endswith(valid_extensions)]
    
    # Se não tiver imagem, cria uma de teste
    if not images:
        print("Nenhuma imagem encontrada na pasta input_images.")
        test_img_path = os.path.join(input_folder, "teste_01.jpg")
        create_test_image(test_img_path)
        images = ["teste_01.jpg"]
    
    # Pega a primeira imagem para testar
    img_name = images[0]
    input_path = os.path.join(input_folder, img_name)
    output_filename = f"video_{os.path.splitext(img_name)[0]}.mp4"
    output_path = os.path.join(output_folder, output_filename)
    
    print(f"--- Iniciando Processamento ---")
    print(f"Imagem: {img_name}")
    print(f"Duração: 5 segundos")
    
    # Cria o clipe base (apenas para referência de duração)
    clip = ImageClip(input_path).with_duration(5)
    
    # Aplica o Zoom (passando o caminho da imagem explicitamente)
    # Aumentei para 0.2 (20% por segundo) para ser bem visível
    video = zoom_in_effect(clip, input_path, zoom_ratio=0.2)
    
    # Configurações de exportação para YouTube Shorts
    video.with_fps(30).write_videofile(output_path, codec='libx264', audio=False, preset='ultrafast')
    
    print(f"--- Concluído ---")
    print(f"Vídeo salvo em: {output_path}")

if __name__ == "__main__":
    processar_video()
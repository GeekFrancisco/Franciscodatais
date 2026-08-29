import os
import pandas as pd

def criar_roteiro_automatico():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    roteiro_path = os.path.join(base_dir, "roteiros", "roteiro_versiculos.xlsx")
    img_dir = os.path.join(base_dir, "input_images")
    
    os.makedirs(os.path.dirname(roteiro_path), exist_ok=True)
    
    # Procura imagens reais na sua pasta
    imagens = [f for f in os.listdir(img_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not imagens:
        print("AVISO: Nenhuma imagem encontrada em 'input_images'. Coloque imagens lá!")
        imagem_usar = "exemplo.jpg"
    else:
        imagem_usar = imagens[0] # Pega a primeira imagem que achar
        print(f"Imagem detectada: {imagem_usar}")

    # Cria dados de exemplo com versículos reais
    data = {
        "Idioma": ["EN", "ES", "PT"],
        "Imagem": [imagem_usar, imagem_usar, imagem_usar],
        "Texto": [
            "The Lord is my shepherd; I shall not want. He maketh me to lie down in green pastures.", 
            "Jehová es mi pastor; nada me faltará. En lugares de delicados pastos me hará descansar.",
            "O Senhor é o meu pastor, nada me faltará. Deitar-me faz em verdes pastos."
        ],
        "Titulo": [
            "THE LORD IS MY SHEPHERD", 
            "JEHOVÁ ES MI PASTOR", 
            "O SENHOR É MEU PASTOR"
        ],
        "Subtitulo": ["Psalm 23", "Salmo 23", "Salmo 23"],
        "MarcaDagua": ["@dailybibleverses-d5", "@VersículoBíblicoDiario", "@VersículoBíblicoDiario"]
    }
    
    df = pd.DataFrame(data)
    df.to_excel(roteiro_path, index=False)
    print(f"✅ Roteiro criado com sucesso em: {roteiro_path}")
    print("Agora você pode rodar o gerador!")

if __name__ == "__main__":
    criar_roteiro_automatico()
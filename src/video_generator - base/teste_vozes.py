import asyncio
import edge_tts
import os

# Textos bíblicos para teste
TEXTO_PT = "O Senhor é o meu pastor, nada me faltará. Deitar-me faz em verdes pastos."
TEXTO_EN = "The Lord is my shepherd; I shall not want. He maketh me to lie down in green pastures."
TEXTO_ES = "Jehová es mi pastor; nada me faltará. En lugares de delicados pastos me hará descansar."

# Vozes Sugeridas (Masculinas e Neurais)
# PT: Antonio (BR)
# EN: Guy (US) ou Christopher (US)
# ES: Alvaro (ES) ou Alonso (US)

async def gerar_audio(texto, voz, arquivo_saida):
    print(f"Gerando áudio em {arquivo_saida} com a voz {voz}...")
    communicate = edge_tts.Communicate(texto, voz)
    await communicate.save(arquivo_saida)
    print("Concluído!")

async def main():
    # Cria pasta de testes se não existir
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "testes_audio")
    os.makedirs(output_dir, exist_ok=True)

    # 1. Teste Português (Antonio)
    await gerar_audio(TEXTO_PT, "pt-BR-AntonioNeural", os.path.join(output_dir, "teste_pt_antonio.mp3"))
    
    # 2. Teste Inglês (Christopher)
    await gerar_audio(TEXTO_EN, "en-US-ChristopherNeural", os.path.join(output_dir, "teste_en_christopher.mp3"))
    
    # 3. Teste Espanhol (Alvaro)
    await gerar_audio(TEXTO_ES, "es-ES-AlvaroNeural", os.path.join(output_dir, "teste_es_alvaro.mp3"))

    print("\n--- Testes Finalizados ---")
    print(f"Verifique a pasta: {output_dir}")

if __name__ == "__main__":
    asyncio.run(main())
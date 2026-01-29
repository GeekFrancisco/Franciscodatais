import os
import re

def verificar_falhas():
    # Caminho do log (ajustado para rodar da raiz ou da pasta scripts)
    log_path = os.path.join("logs", "ultimo_log.txt")
    if not os.path.exists(log_path):
        # Tenta achar subindo um nível caso esteja rodando de dentro de scripts
        log_path = os.path.join("..", "logs", "ultimo_log.txt")
        
    if not os.path.exists(log_path):
        print("❌ Arquivo de log não encontrado!")
        print("Certifique-se de que você rodou o gerador de Shorts pelo menos uma vez.")
        return

    print(f"🔍 Analisando log: {log_path} ...\n")

    shorts_sem_audio = []
    shorts_com_erro_geral = []
    
    current_short = None
    
    # Padrões de erro para buscar
    erro_audio_pattern = "Áudio não foi gerado"
    erro_tts_pattern = "Erro no TTS"
    short_header_pattern = r"--- Processando Short (\d+)"

    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            # Identifica qual Short está sendo processado
            match = re.search(short_header_pattern, line)
            if match:
                current_short = int(match.group(1))
            
            # Se achou erro de áudio no bloco atual
            if current_short:
                if erro_audio_pattern in line or erro_tts_pattern in line:
                    if current_short not in shorts_sem_audio:
                        shorts_sem_audio.append(current_short)

    if not shorts_sem_audio:
        print("✅ Tudo parece certo! Nenhum erro de áudio detectado no último log.")
    else:
        print(f"⚠️  ATENÇÃO: {len(shorts_sem_audio)} Shorts apresentaram falhas de áudio/TTS.")
        print(f"   Shorts afetados: {shorts_sem_audio}")
        print("\n🛠️  COMANDO PARA CORRIGIR (Copie e cole):")
        lista_str = " ".join(str(n) for n in sorted(shorts_sem_audio))
        print(f"\npython src/generators/shorts_generator.py {lista_str}")
        print("\n")
    return shorts_sem_audio

if __name__ == "__main__":
    verificar_falhas()

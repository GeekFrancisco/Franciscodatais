import wave
import math
import struct
import os

def generate_bell_sound(filepath):
    # Garante diretório
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    sample_rate = 44100
    duration = 2.0 # 2 segundos
    frequency = 1200.0 # 1.2kHz (Sino brilhante)

    num_samples = int(sample_rate * duration)
    
    with wave.open(filepath, 'w') as wav_file:
        wav_file.setnchannels(1) # Mono
        wav_file.setsampwidth(2) # 2 bytes (16 bit)
        wav_file.setframerate(sample_rate)
        
        for i in range(num_samples):
            t = float(i) / sample_rate
            
            # Envelope (Ataque rápido, Decay longo exponencial)
            envelope = math.exp(-3 * t)
            
            # Onda: Fundamental + Harmônicos
            value = 0.6 * math.sin(2 * math.pi * frequency * t)
            value += 0.3 * math.sin(2 * math.pi * (frequency * 1.5) * t) # Quinta
            value += 0.1 * math.sin(2 * math.pi * (frequency * 2.0) * t) # Oitava
            
            # Normaliza para 16-bit
            sample = value * envelope * 32000.0
            
            # Clamp
            if sample > 32767: sample = 32767
            if sample < -32768: sample = -32768
                
            wav_file.writeframes(struct.pack('h', int(sample)))

    print(f"Gerado SFX: {filepath}")

if __name__ == "__main__":
    # Caminho de destino na pasta assets
    # Como este script está em utils/, assets está em ../assets
    base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(os.path.dirname(base_dir), "assets")
    
    # Salvar como MP3 (na verdade é WAV, mas o MoviePy deve lidar)
    # Se formos puristas, salvamos como .wav e mudamos o script principal para aceitar wav
    target_path = os.path.join(assets_dir, "subscribe.mp3") 
    
    generate_bell_sound(target_path)
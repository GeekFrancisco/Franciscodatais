import os
import wave
import math
import struct
import asyncio
import edge_tts
from mutagen.mp3 import MP3

async def generate_audio_and_word_timings(text, voice, audio_path, rate="-10%"):
    """
    Gera áudio usando edge-tts e retorna os tempos exatos de cada palavra.
    Suporta textos longos dividindo em chunks para evitar timeout/limites.
    """
    # Limite de segurança (caracteres) para cada chunk
    CHUNK_LIMIT = 2500 
    
    # Se o texto for pequeno, processa direto (mais rápido)
    if len(text) < CHUNK_LIMIT:
        # Retry logic for short texts
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = await _generate_audio_segment(text, voice, audio_path, rate, 0)
                if result:
                    return result
            except Exception as e:
                print(f"      ⚠️ Erro de conexão (Tentativa {attempt+1}/{max_retries}): {e}")
                await asyncio.sleep(2)
        print("      ❌ Falha definitiva após 3 tentativas.")
        return None

    print(f"📜 Texto longo detectado ({len(text)} chars). Dividindo em partes...")
    
    # Divide o texto em sentenças para não cortar frases no meio
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < CHUNK_LIMIT:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    print(f"✂️ Texto dividido em {len(chunks)} partes.")
    
    all_timings = []
    total_duration_so_far = 0.0
    combined_audio_data = bytearray()
    
    # Processa cada chunk sequencialmente
    for i, chunk_text in enumerate(chunks):
        if not chunk_text: continue
        
        temp_chunk_path = f"{audio_path}.part{i}.mp3"
        print(f"   🎙️ Processando parte {i+1}/{len(chunks)}...")
        
        # Tenta gerar áudio com retry
        chunk_timings = None
        max_retries = 3
        for attempt in range(max_retries):
            try:
                chunk_timings = await _generate_audio_segment(chunk_text, voice, temp_chunk_path, rate, total_duration_so_far)
                if chunk_timings:
                    break # Sucesso
            except Exception as e:
                print(f"      ⚠️ Tentativa {attempt+1}/{max_retries} falhou: {e}")
                await asyncio.sleep(2) # Espera um pouco antes de tentar de novo
        
        if chunk_timings is not None:
            all_timings.extend(chunk_timings)
            
            # Lê o áudio gerado e adiciona ao buffer final
            if os.path.exists(temp_chunk_path):
                with open(temp_chunk_path, "rb") as f:
                    chunk_data = f.read()
                    combined_audio_data.extend(chunk_data)
                
                # Pega a duração real deste pedaço para somar no offset do próximo
                chunk_duration = get_audio_duration(temp_chunk_path)
                total_duration_so_far += chunk_duration
                
                # Remove arquivo temporário
                try:
                    os.remove(temp_chunk_path)
                except:
                    pass
        else:
            print(f"⚠️ Falha ao gerar áudio da parte {i+1}")

    # Salva o arquivo de áudio final combinado
    with open(audio_path, "wb") as final_file:
        final_file.write(combined_audio_data)
        
    print(f"✅ Áudio completo gerado: {total_duration_so_far:.2f}s")
    return all_timings

async def _generate_audio_segment(text, voice, audio_path, rate, time_offset=0):
    """Função auxiliar para gerar áudio de um segmento."""
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    word_timings = []
    
    if os.path.exists(audio_path):
        os.remove(audio_path)

    try:
        with open(audio_path, "wb") as file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    start_sec = (chunk["audio_offset"] / 10_000_000) + time_offset
                    duration_sec = chunk["duration"] / 10_000_000
                    word_len = chunk["word_length"]
                    text_offset = chunk["text_offset"]
                    word = text[text_offset : text_offset + word_len]
                    
                    # Heurística para incluir asteriscos se foram ignorados pelo TTS
                    # Necessário para o sistema de destaque (Highlight)
                    start_idx = text_offset
                    end_idx = text_offset + word_len
                    
                    # Checa caractere anterior
                    if start_idx > 0 and text[start_idx-1] == '*':
                        start_idx -= 1
                    
                    # Checa caractere posterior
                    if end_idx < len(text) and text[end_idx] == '*':
                        end_idx += 1
                        
                    word = text[start_idx : end_idx]
                    
                    word_timings.append({
                        "word": word,
                        "start": start_sec,
                        "end": start_sec + duration_sec
                    })
        return word_timings
    except Exception as e:
        print(f"Erro no TTS (segmento): {e}")
        return None

def estimate_word_timings(text, duration):
    """
    Fallback: Estima tempos das palavras linearmente.
    """
    words = text.split()
    if not words: return []
    
    avg_duration = duration / len(words)
    timings = []
    current_time = 0
    
    for word in words:
        timings.append({
            "word": word,
            "start": current_time,
            "end": current_time + avg_duration
        })
        current_time += avg_duration
        
    return timings

def get_audio_duration(file_path):
    try:
        return MP3(file_path).info.length
    except:
        return 0

def generate_bell_sfx(filepath):
    """Gera um efeito sonoro de 'Sino' sintético (WAV)."""
    if os.path.exists(filepath): return
    
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        sample_rate = 44100
        duration = 1.5
        frequency = 1000.0 # 1kHz (Sino)

        num_samples = int(sample_rate * duration)
        
        with wave.open(filepath, 'w') as wav_file:
            wav_file.setnchannels(1) 
            wav_file.setsampwidth(2) 
            wav_file.setframerate(sample_rate)
            
            for i in range(num_samples):
                t = float(i) / sample_rate
                envelope = math.exp(-5 * t)
                
                value = 0.5 * math.sin(2 * math.pi * frequency * t)
                value += 0.3 * math.sin(2 * math.pi * (frequency * 2) * t)
                
                sample = value * envelope * 32000.0
                sample = max(-32768, min(32767, sample))
                
                wav_file.writeframes(struct.pack('h', int(sample)))
                
        print(f"SFX gerado: {filepath}")
    except Exception as e:
        print(f"Erro ao gerar SFX: {e}")

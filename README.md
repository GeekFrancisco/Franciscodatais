# Automated Video Generator

Este projeto automatiza a criação de vídeos **Shorts (9:16)** e **Longos (16:9)** usando:
- Imagens estáticas com efeito **Ken Burns** (zoom/pan suave)
- Narração TTS via **Edge-TTS** (inglês, espanhol e português)
- Legendas sincronizadas on-screen
- Música de fundo e CTA final (AMEN / INSCREVA-SE / etc.)

Toda a lógica nova está centralizada em `src/` e em uma planilha única `Roteiro_Geral.xlsx`.

---

## Estrutura do Projeto

- **src/**
  - **configs/**
    - [settings.py](file:///c:/Users/franciscoj/Python_Initial/Automated_Video_Generator/src/configs/settings.py)  
      Caminhos globais, fontes e vozes TTS.
    - [shorts.py](file:///c:/Users/franciscoj/Python_Initial/Automated_Video_Generator/src/configs/shorts.py)  
      Configurações visuais e de tempo dos vídeos **Shorts**.
    - [longs.py](file:///c:/Users/franciscoj/Python_Initial/Automated_Video_Generator/src/configs/longs.py)  
      Configurações dos vídeos **Longos**.
  - **generators/**
    - [shorts_generator.py](src/generators/shorts_generator.py)  
      Lê a aba **Shorts** do Excel e gera vídeos verticais 1080x1920.
    - [longs_generator.py](src/generators/longs_generator.py)  
      Lê a aba **Longos** do Excel e gera vídeos horizontais 1920x1080.
    - [publish_shorts.py](src/generators/publish_shorts.py)
      Lógica de upload para o YouTube via API.
  - **utils/**
    - [audio_utils.py](src/utils/audio_utils.py)  
      Geração de áudio TTS e cálculo de tempos por palavra.
    - [video_utils.py](src/utils/video_utils.py)  
      Funções de thumbnail, textos e efeito Ken Burns.

- **scripts/**
  - [validate_roteiro.py](scripts/validate_roteiro.py)
    Verifica se a planilha tem erros (imagens faltando, colunas vazias) antes de gerar.
  - [publish_youtube_from_planilha.py](scripts/publish_youtube_from_planilha.py)
    Script principal para publicar vídeos pendentes no YouTube.
  - [update_roteiro_shorts_columns.py](scripts/update_roteiro_shorts_columns.py)
    Garante que a planilha tenha todas as colunas de publicação necessárias.
  - [list_channels.py](scripts/list_channels.py)
    Lista canais conectados ou ajuda na autenticação inicial.

- **secrets/**
  - Onde você coloca o `client_secret_youtube.json` baixado do Google Cloud.

- **tokens/**
  - Onde os tokens de acesso (login) dos canais são salvos (ex: `youtube_en.json`, `youtube_es.json`).


- **SHORTS/**
  - `input_images/` → imagens base para vídeos curtos.
  - `output_videos_finais/` → onde os vídeos Shorts prontos são salvos.

- **LONGOS/**
  - `input_images/` → imagens base para vídeos longos (slideshow).
  - `output_videos/` → onde os vídeos longos prontos são salvos.

- **assets/**
  - Músicas de fundo (`.mp3`) e efeitos sonoros (ex: sino do Subscribe).

- **temp_audios/**
  - Áudios TTS gerados temporariamente (`short_audio_X.mp3`, `long_audio_X.mp3`).

- **roteiros/**
  - [Roteiro_Geral.xlsx](file:///c:/Users/franciscoj/Python_Initial/Automated_Video_Generator/roteiros/Roteiro_Geral.xlsx)  
    Planilha única com abas **Shorts** e **Longos**.

---

## Instalação

1. Instale o **Python 3.8+**.
2. Dentro da pasta do projeto, instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

3. Certifique-se de ter o **ImageMagick** instalado se aparecerem erros do MoviePy ao trabalhar com textos/imagens.
4. É necessário **acesso à internet** para o Edge-TTS (geração de voz).

---

## Fluxo Geral (Planilha Única)

O projeto usa **um único Excel**:  
`roteiros/Roteiro_Geral.xlsx` com duas abas:

- Aba **Shorts** → controla todos os vídeos verticais.
- Aba **Longos** → controla todos os vídeos horizontais.

Cada linha da aba representa **um vídeo** (Short ou Longo), com:
- `Idioma` → EN, ES ou PT
- `Texto` → texto completo da narração
- `Titulo` → título principal do vídeo
- `Subtitulo` → legenda/título final opcional (últimos segundos)
- `Imagem` → nome do arquivo de imagem na pasta `input_images`
- `TextoThumb` → frase de impacto para a thumbnail (se vazio, cai no `Titulo`)
- `MarcaDagua` → texto da marca d’água (ex: @seucanal)

---

## Validação Prévia (Recomendado)

Antes de gerar os vídeos, você pode verificar se está tudo certo com a planilha (imagens faltando, textos vazios, colunas incorretas):

```bash
python scripts/validate_roteiro.py
```

Isso evita erros no meio do processamento, garantindo que todas as imagens citadas na planilha existam nas pastas corretas.

---

## Como Gerar Shorts (Vídeos Verticais 1080x1920)

1. Preencha a aba **Shorts** em  
   [Roteiro_Geral.xlsx](file:///c:/Users/franciscoj/Python_Initial/Automated_Video_Generator/roteiros/Roteiro_Geral.xlsx):

   Campos principais por linha:
   - `Idioma` → EN / ES / PT
   - `Texto` → o texto completo da narração
   - `Titulo` → texto grande no topo do vídeo
   - `Subtitulo` → frase que aparece nos últimos 2,5s
   - `TextoThumb` → frase da thumbnail
   - `Imagem` → nome da imagem em `SHORTS/input_images`
   - `MarcaDagua` → @do canal (topo/rodapé, opacidade ajustada no código)

2. Coloque as imagens correspondentes em:

   ```text
   SHORTS/input_images/
   ```

3. Gere os vídeos executando:

   ```bash
   # Estando na raiz do projeto
   python -m venv .venv
   .venv\Scripts\activate

   python src/generators/shorts_generator.py
   ```

4. Os vídeos prontos serão salvos em:

   ```text
   SHORTS/output_videos_finais/
   ```

### Comportamento dos Shorts

- **Formato:** 1080x1920 (9:16).
- **Título principal:**
  - Fonte bold (Montserrat/Arial Bold), ~80px, branco com contorno preto.
  - No topo (y ≈ 120px), no máximo 2 linhas.

- **Legendas dinâmicas:**
  - Geradas a partir dos tempos de palavra do TTS.
  - Cada bloco fica ~2–3s na tela.
  - `SUBTITLE_OFFSET = -0.12` → legenda aparece ~0,12s antes da voz (melhor leitura).
  - Posicionadas na parte inferior (y ≈ 1450px).

- **Legenda final (Subtitulo/Titulo):**
  - Entra **2,5s antes** do fim do vídeo.
  - Fonte bold, tamanho ~54px, centralizado na parte inferior.

- **CTA final (Subscribe / AMEN / etc.):**
  - Usando `SUBSCRIBE_TEXTS` em [shorts.py](file:///c:/Users/franciscoj/Python_Initial/Automated_Video_Generator/src/configs/shorts.py):
    - EN: `"AMEN"`, `"WRITE AMEN"`, `"LET’S PRAY"`
    - PT: `"INSCREVA-SE"`
    - ES: `"AMÉN"`, `"ESCRIBE AMÉN"`, `"VAMOS A ORAR"`
  - Tamanho grande (`FONT_SIZE_SUBSCRIBE`), branco com contorno preto.
  - Aparece nos últimos 3s (controlado por `PADDING_END`).

- **Narração (voz):**
  - Vozes definidas em [settings.py](file:///c:/Users/franciscoj/Python_Initial/Automated_Video_Generator/src/configs/settings.py):
    - EN: `en-US-ChristopherNeural` com `VOICE_RATE = "-10%"`
    - ES: `es-ES-AlvaroNeural` com velocidade `"+0%"` (ajustada no gerador)
    - PT: `pt-BR-AntonioNeural` com `VOICE_RATE = "-10%"`
  - Áudio é gerado em `temp_audios/short_audio_X.mp3` e depois mixado com a música de fundo.

- **Música de fundo:**
  - Usa um `.mp3` padrão em `assets/`:
    - `Pulsar - The Grey Room _ Density & Time.mp3`
  - É estendida/loopada para cobrir a duração total do vídeo.

---

## Como Gerar Vídeos Longos (Horizontais 1920x1080)

1. Preencha a aba **Longos** em  
   [Roteiro_Geral.xlsx](file:///c:/Users/franciscoj/Python_Initial/Automated_Video_Generator/roteiros/Roteiro_Geral.xlsx):

   Campos típicos:
   - `Idioma`, `Texto`, `Titulo`, `Subtitulo`
   - Colunas de tema visual e imagens conforme configurado no projeto.

2. Coloque as imagens em:

   ```text
   LONGOS/input_images/
   ```

3. Execute:

   ```bash
   # Ambiente virtual já ativado
   python src/generators/longs_generator.py
   ```

4. Os vídeos serão salvos em:

   ```text
   LONGOS/output_videos/
   ```

Os longos usam:
- Formato 1920x1080
- Slideshow com Ken Burns lento
- Narração TTS + legendas sincronizadas
- Configurações específicas em [longs.py](file:///c:/Users/franciscoj/Python_Initial/Automated_Video_Generator/src/configs/longs.py)

---

## Notas e Dicas

- **Internet obrigatória** para o Edge-TTS. Se a conexão falhar, o gerador tenta fallback com estimativa de tempos.
- Se a música de fundo faltar em `assets/`, o vídeo ainda é gerado apenas com narração.
- Em caso de erro estranho de MoviePy, verifique:
  - Instalação do ImageMagick
  - Versão do MoviePy e compatibilidade com o Python
- Áudios temporários podem ser apagados sem problemas:

  ```bash
  del temp_audios\*.mp3
  ```

Isso força a regeneração das narrações na próxima execução.

---

## Publicação Automática no YouTube

O projeto possui integração completa com a API do YouTube para upload automático de vídeos **Shorts** (e Longos, se configurado).

### 1. Preparação da Planilha

Certifique-se de que sua planilha tenha as colunas de controle de publicação. Se não tiver certeza, rode:

```bash
python scripts/update_roteiro_shorts_columns.py
```

Isso adicionará colunas como:
- `Plataforma`: Define o canal de destino (ex: `EN`, `ES`, `PT`).
- `Publicar`: Marque como `SIM` para publicar.
- `StatusPublicacao`: O script muda de `PENDENTE` para `PUBLICADO` automaticamente.
- `DataPublicacao` e `HoraPublicacao`: Para agendamento.
- `TituloShort`, `DescricaoShort`, `Hashtags`.

### 2. Configuração de Credenciais

1. **Google Cloud**: Crie um projeto, ative a **YouTube Data API v3** e crie credenciais OAuth (Desktop App).
2. **Secrets**: Salve o JSON baixado como `secrets/client_secret_youtube.json`.
3. **Autenticação**:
   A primeira vez que rodar, o script pedirá para autenticar no navegador.
   Os tokens serão salvos em `tokens/` baseados no código do canal (ex: `youtube_en.json` para plataforma `EN`).

### 3. Executando a Publicação

Para publicar todos os vídeos marcados com `Publicar = SIM` e `StatusPublicacao = PENDENTE`:

```bash
python scripts/publish_youtube_from_planilha.py
```

O script irá:
1. Ler a planilha.
2. Identificar o arquivo de vídeo gerado.
3. Fazer o upload para o canal correspondente (baseado na coluna `Plataforma`).
4. Aplicar título, descrição, tags e data de agendamento.
5. Atualizar a planilha com o ID do vídeo e link.

---

## Uso com Outras Plataformas (TikTok, Instagram)


O TikTok não possui uma API pública simples e estável para qualquer conta pessoal publicar como o YouTube. O fluxo recomendado neste projeto é:

- Usar o gerador para criar:
  - Vídeo vertical (`SHORTS/output_videos_finais/`)
  - Thumbnail (se desejar usar como capa no TikTok)
- Na planilha, você pode usar colunas como:
  - `TituloShort` → serve como ideia de título/caption
  - `Hashtags` → copiar/colar na descrição do TikTok

Fluxo prático:
- Gerar todos os vídeos com o script de Shorts.
- No celular ou desktop:
  - Abrir TikTok
  - Subir o `.mp4` correspondente
  - Copiar/colar título/hashtags a partir do que está na planilha (ou exportar a planilha para facilitar).

No futuro, se você usar alguma ferramenta externa ou API específica de parceiro TikTok, é possível integrar um script que leia a mesma planilha e faça chamadas para essa ferramenta.

### 4. Uso com Instagram (Reels)

Para Instagram Reels, o cenário é parecido:

- A API oficial de upload (Graph API) exige:
  - **Conta Business** ou Creator conectada a uma **Página do Facebook**
  - Configuração de App no **Facebook Developer**
- Este projeto, por enquanto, assume fluxo **semiautomático**:
  - Gera o vídeo vertical e a thumbnail
  - Você faz o upload manualmente no Instagram (Reels)

Sugestão de uso:
- Usar colunas da planilha para alinhar textos:
  - `TituloShort` → frase principal do Reels
  - `DescricaoShort` / `Hashtags` → texto e hashtags da legenda
- Ao publicar:
  - Abrir a planilha
  - Copiar/colar as legendas e hashtags
  - Escolher a capa (thumbnail) se desejar (a partir do arquivo gerado).

### 5. Estratégia recomendada

- **YouTube**:
  - Foco em automação total (API oficial, tokens por canal, controle via planilha).
- **TikTok / Instagram**:
  - Usar os mesmos vídeos e textos gerados aqui.
  - Publicação manual ou via ferramentas externas (Creator Studio / Business Suite / agendadores).
  - A planilha funciona como “central” de títulos, descrições e hashtags para todas as plataformas.

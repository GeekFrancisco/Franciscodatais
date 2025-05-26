import docx
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from nltk.corpus import stopwords
from collections import Counter
import nltk
import string
import random

# Baixa os stopwords em português
nltk.download('stopwords')
stop_words = set(stopwords.words('portuguese'))
stop_words.update(['ti', 'peti'])  # Remover essas também

# Função para ler o conteúdo de um arquivo .docx
def ler_arquivo_word(caminho_arquivo):
    doc = docx.Document(caminho_arquivo)
    texto = ''
    for paragrafo in doc.paragraphs:
        texto += paragrafo.text + ' '
    return texto

# Caminho para seu arquivo Word
caminho = 'Modelo Book_do_PETI 20052025.docx'
texto = ler_arquivo_word(caminho)

# Processa o texto: remove pontuação e stopwords
palavras = texto.split()
pontuacoes = string.punctuation + "“”‘’–—"

palavras_filtradas = [
    palavra.lower().strip(pontuacoes) 
    for palavra in palavras 
    if palavra.lower().strip(pontuacoes) not in stop_words
]

# Conta a frequência das palavras
frequencia = Counter(palavras_filtradas)

# Remove se veio "peti" do texto e adiciona centralizado e grande
frequencia = {k: v for k, v in frequencia.items() if k != 'peti'}
frequencia['PETI'] = 750  # Deixa PETI bem visível

# Função de cor suave em tons de cinza claro
def cor_cinza_suave(*args, **kwargs):
    nivel = random.randint(130, 180)  # Cinzas mais claros: 130–180 (0 é preto, 255 é branco)
    return f"rgb({nivel},{nivel},{nivel})"

# Gera nuvem com cor personalizada (tons de cinza claro)
nuvem = WordCloud(
    width=2480,
    height=3508,
    background_color='white',
    color_func=cor_cinza_suave,
    prefer_horizontal=1.0,
    collocations=False
).generate_from_frequencies(frequencia)

# Exibe com tamanho A4
plt.figure(figsize=(8.27, 11.69))  # Tamanho A4
plt.imshow(nuvem, interpolation='bilinear')
plt.axis('off')
plt.tight_layout()
plt.show()

# Salva imagem se quiser usar como fundo
nuvem.to_file("nuvem_petisutil.png")

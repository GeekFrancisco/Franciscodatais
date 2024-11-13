import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

# Carregar o arquivo CSV com o separador correto
file_path = 'Base/CHATGPT.csv'
df = pd.read_csv(file_path, sep=';')

# Agrupar os dados pela coluna 'Nome' e contar a quantidade de acessos
acessos_por_nome = df.groupby('Nome').size()

# Calcular o número total de usuários e o total de acessos
total_usuarios = acessos_por_nome.size
total_acessos = acessos_por_nome.sum()

# Dividir os acessos de "FranciscoJ" por 4, mas apenas se o resultado for inteiro
acessos_por_nome_modificado = acessos_por_nome.copy()

# Filtrar os nomes com mais de 400 acessos
acessos_maior_que_400 = acessos_por_nome_modificado[acessos_por_nome_modificado > 400]

# Calcular a média dos acessos maiores que 400
media_acessos = acessos_maior_que_400.mean()

# Exibir a média e a soma total dos acessos para conferir
print(f'Média de Interações por nome (com divisões aplicadas): {media_acessos}')
print(f'Soma total de Interações: {total_acessos}')

# Função para determinar a cor com base no valor de acessos
def cor_por_faixa(acessos):
    if acessos <= 1500:
        return '#ADD8E6'  # Azul claro
    elif 1501 <= acessos <= 3500:
        return '#4682B4'  # Azul médio
    else:
        return '#00008B'  # Azul escuro

# Criar o gráfico de barras para Acessos Maior que 400
fig, ax = plt.subplots(figsize=(10, 6))

# Plotar as barras com cores diferentes com base nas faixas de acessos
barras = acessos_maior_que_400.plot(kind='bar', color=[cor_por_faixa(v) for v in acessos_maior_que_400], ax=ax)

# Adicionar rótulos de dados nas barras
for i, v in enumerate(acessos_maior_que_400):
    barras.text(i, v + 1, str(round(v, 0)), ha='center', va='bottom', fontsize=10, color='gray')

# Adicionar linha horizontal representando a média
ax.axhline(y=media_acessos, color='r', linestyle='--', label=f'Média ({media_acessos:.0f})')

# Adicionar o rótulo da média fora do gráfico, no canto superior direito
plt.text(1.01, media_acessos, f'{media_acessos:.0f}', color='r', ha='left', va='center', transform=ax.get_yaxis_transform(), fontsize=10, fontweight='bold')

# Calcular o número total de usuários distintos e o total de acessos
total_usuarios_distintos = acessos_por_nome.index.nunique()
total_acessos = acessos_por_nome.sum()

# Ajustar o título para incluir a quantidade total de usuários únicos e acessos
ax.set_title(f'Interações no ChatGPT nos Últimos 48 Dias (Usuários com mais de 400 Interações)\nTotal Global: {total_usuarios_distintos} Usuários, {total_acessos} Interações', fontsize=14)


# Adicionar rótulos nos eixos
ax.set_xlabel('Nomes', fontsize=12)
ax.set_ylabel('Interações', fontsize=12)
ax.set_xticklabels(acessos_maior_que_400.index, rotation=45, ha='right')

# Criar a barra de cores com tonalidades de azul
cmap = mpl.colors.ListedColormap(['#ADD8E6', '#4682B4', '#00008B'])
bounds = [0, 1500, 3500, max(acessos_maior_que_400)]
norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])

# Adicionar a colorbar ao gráfico
fig.colorbar(sm, ax=ax, label='Faixa de Interações')

# Adicionar a legenda
ax.legend(title='Legenda', labels=['Média', 'Interações'], loc='upper left')

# Ajustar o layout para evitar sobreposição
plt.tight_layout()

# Mostrar o gráfico
plt.show()

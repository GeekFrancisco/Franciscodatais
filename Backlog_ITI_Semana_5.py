# Backlog SPN
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

# Caminho para a planilha na pasta raiz do projeto
file_path = 'Base\Backlog_5.xlsx'

# Tentar carregar a aba 'SPN' da planilha "Backlog.xlsx"
try:
    df = pd.read_excel(file_path, sheet_name='ITI')
except FileNotFoundError:
    print(f"Erro: O arquivo '{file_path}' não foi encontrado.")
    exit()
except ValueError:
    print("Erro: A aba 'SPN' não existe no arquivo.")
    exit()

# Converter a coluna 'Backlog' para datetime, com tratamento de erro
try:
    df['Backlog'] = pd.to_datetime(df['Backlog'])
except Exception as e:
    print(f"Erro ao converter a coluna 'Backlog': {e}")
    exit()

# Criar um PDF para salvar os gráficos
pdf_path = "Graficos_Backlog_ITI_Semana_05.pdf"
pdf = PdfPages(pdf_path)

# Configurar o layout da página com vários gráficos (ex: 2 linhas e 2 colunas)
fig, axs = plt.subplots(2, 2, figsize=(12, 10))  # 2x2 grid de gráficos

# Adicionar título global à página
fig.suptitle('Análise Backlog ITI - Semana 04/11 a 08/11', fontsize=16)

# Função auxiliar para adicionar rótulos de dados
def add_labels_bars(ax):
    """Adiciona rótulos de dados nas barras do gráfico."""
    for p in ax.patches:
        ax.annotate(f'{p.get_height()}', (p.get_x() + p.get_width() / 2, p.get_height()), ha='center', va='bottom')

def add_labels_line(ax, x_data, y_data):
    """Adiciona rótulos de dados nas linhas do gráfico."""
    for i, (x, y) in enumerate(zip(x_data, y_data)):
        ax.annotate(f'{y}', (x, y), textcoords="offset points", xytext=(0,5), ha='center')

# Gráfico 1: Quantidade de incidentes por setor (total e resolvidos)
df_total_sector = df['Setor'].value_counts()  # Total de incidentes por setor
df_resolved = df[df['Status'] == 'Concluido']  # Filtrar apenas os resolvidos
df_resolved_sector = df_resolved['Setor'].value_counts()  # Total de incidentes resolvidos por setor

# Calcular o total de incidentes não resolvidos
df_unresolved_sector = df_total_sector - df_resolved_sector.reindex(df_total_sector.index, fill_value=0)

# Criar um gráfico de barras com três conjuntos de dados
bar_width = 0.25  # Largura das barras
indices = np.arange(len(df_total_sector.index))  # Índices para as barras

# Adicionar as barras ao gráfico
axs[0, 0].bar(indices, df_total_sector.values, width=bar_width, color='skyblue', label='Total')
axs[0, 0].bar(indices + bar_width, df_resolved_sector.reindex(df_total_sector.index, fill_value=0).values, 
               width=bar_width, color='lightgreen', label='Resolvidos')
axs[0, 0].bar(indices + 2 * bar_width, df_unresolved_sector.values, width=bar_width, 
               color='salmon', label='Pendentes')
axs[0, 0].set_title('Comparativo entre Total, Resolvidos e Pendentes')
axs[0, 0].set_xlabel('Chamados')
axs[0, 0].set_ylabel('Quantidade')
axs[0, 0].set_xticks(indices + bar_width)  # Ajustar os ticks do eixo x
axs[0, 0].set_xticklabels(df_total_sector.index, rotation=45)  # Nomes dos setores
axs[0, 0].legend()  # Adicionar legenda

# Adicionar os valores dentro das barras
for i, total in enumerate(df_total_sector.values):
    # Para a barra 'Total'
    axs[0, 0].text(i, total / 2, str(total), ha='center', va='center', color='black')  # Total no meio
    axs[0, 0].text(i, (total / 2) - 1, f'({(total / total * 100):.1f}%)',  # Percentual logo abaixo do Total
                   ha='center', va='top', color='black')  

for i, resolved in enumerate(df_resolved_sector.reindex(df_total_sector.index, fill_value=0).values):
    # Para as barras 'Resolvidos'
    axs[0, 0].text(i + bar_width, resolved / 2, str(resolved), ha='center', va='center', color='black')  # Resolvidos no meio
    axs[0, 0].text(i + bar_width, (resolved / 2) - 1, f'({(resolved / df_total_sector.iloc[i] * 100):.1f}%)', 
                   ha='center', va='top', color='black')  # Percentual logo abaixo dos Resolvidos

for i, unresolved in enumerate(df_unresolved_sector.values):
    # Para as barras 'Pendentes'
    axs[0, 0].text(i + 2 * bar_width, unresolved / 2, str(unresolved), ha='center', va='center', color='black')  # Pendentes no meio
    axs[0, 0].text(i + 2 * bar_width, (unresolved / 2) - 1, f'({(unresolved / df_total_sector.iloc[i] * 100):.1f}%)', 
                   ha='center', va='top', color='black')  # Percentual logo abaixo dos Pendentes



# Gráfico 2: Evolução do Backlog ao longo do tempo
# Backlog total
backlog_by_date = df.groupby(df['Backlog'].dt.to_period('M')).size()

# Backlog resolvido
resolved_by_date = df[df['Status'] == 'Concluido'].groupby(df['Backlog'].dt.to_period('M')).size()

# Backlog pendente (não resolvido)
pending_by_date = df[df['Status'] != 'Concluido'].groupby(df['Backlog'].dt.to_period('M')).size()

# Reindexar os dados resolvidos e pendentes para alinhar com o backlog total, preenchendo valores faltantes com 0
resolved_by_date = resolved_by_date.reindex(backlog_by_date.index, fill_value=0)
pending_by_date = pending_by_date.reindex(backlog_by_date.index, fill_value=0)

# Plotar a evolução do backlog
axs[0, 1].plot(backlog_by_date.index.astype(str), backlog_by_date.values, marker='o', color='orange', label='Total')
axs[0, 1].plot(resolved_by_date.index.astype(str), resolved_by_date.values, marker='o', color='lightgreen', label='Resolvidos')
axs[0, 1].plot(pending_by_date.index.astype(str), pending_by_date.values, marker='o', color='red', label='Pendentes')  # Linha para pendentes

# Configurações do gráfico
axs[0, 1].set_title('Evolução do Backlog: Total, Resolvidos e Pendente')
axs[0, 1].set_xlabel('Data do Backlog')
axs[0, 1].set_ylabel('Quantidade')
axs[0, 1].tick_params(axis='x', rotation=45)
axs[0, 1].legend()  # Adicionar legenda

# Adicionar rótulos de dados
add_labels_line(axs[0, 1], backlog_by_date.index.astype(str), backlog_by_date.values)  # Rótulos para total
add_labels_line(axs[0, 1], resolved_by_date.index.astype(str), resolved_by_date.values)  # Rótulos para resolvidos
add_labels_line(axs[0, 1], pending_by_date.index.astype(str), pending_by_date.values)  # Rótulos para pendentes

# Gráfico 3: Distribuição de status dos incidentes (agrupando menores de 5% em "Outros")
df_status = df['Responsavel'].value_counts()

# Calcular porcentagens
total = df_status.sum()
percentages = df_status / total * 100

# Agrupar valores menores que 5% em 'Outros' se houver
df_status_grouped = df_status[percentages >= 5]
other_count = df_status[percentages < 5].sum()

# Adicionar 'Outros' apenas se houver valores menores que 5%
if other_count > 0:
    df_status_grouped['Outros'] = other_count

# Verificar se existem valores para plotar
if not df_status_grouped.empty:
    # Plotar o gráfico de pizza com porcentagens dentro de parênteses
    axs[1, 0].pie(df_status_grouped.values, labels=df_status_grouped.index, 
                  autopct=lambda p: f'({p:.1f}%)', startangle=90, 
                  colors=['lightgreen', 'lightcoral', 'lightblue', 'lightgray', 'gold', 'salmon', 'lavender', 'peachpuff'])
    axs[1, 0].set_title('Distribuição Backlog Responsáveis')
else:
    axs[1, 0].text(0.5, 0.5, 'Nenhum dado disponível', fontsize=12, ha='center', va='center')


# Gráfico 4: Quantidade de incidentes por responsável (gráfico de barras em pé)
df_responsavel = df['Responsavel'].value_counts()
resolved_by_responsavel = df[df['Status'] == 'Concluido']['Responsavel'].value_counts()

# Calculando o percentual de resolvidos
percent_resolved = (resolved_by_responsavel / df_responsavel) * 100
percent_resolved = percent_resolved.fillna(0)  # Preencher NaN com 0

# Configurar as posições das barras
bar_width = 0.4  # Largura das barras
positions = range(len(df_responsavel.index))

# Plotar as barras para a quantidade total de incidentes
total_bars = axs[1, 1].bar(positions, df_responsavel.values, width=bar_width, color='lightseagreen', label='Total')

# Plotar as barras para a quantidade de incidentes resolvidos
resolved_bars = axs[1, 1].bar([p + bar_width for p in positions],
                               resolved_by_responsavel.reindex(df_responsavel.index, fill_value=0).values,
                               width=bar_width, color='lightcoral', label='Resolvidos')

# Configurações do gráfico
axs[1, 1].set_title('Desempenho dos Responsáveis')
axs[1, 1].set_xlabel('Responsáveis')
axs[1, 1].set_ylabel('Quantidade')
axs[1, 1].tick_params(axis='x', rotation=45)  # Rotacionar rótulos do eixo x
axs[1, 1].set_xticks([p + bar_width / 2 for p in positions])  # Ajustar as posições dos rótulos do eixo x
axs[1, 1].set_xticklabels(df_responsavel.index)  # Configurar os rótulos do eixo x

# Adicionar valores dentro das barras de totais
for i, bar in enumerate(total_bars):
    yval = bar.get_height()
    # Colocar apenas o valor dentro da barra
    axs[1, 1].text(bar.get_x() + bar.get_width() / 2, yval / 2, f'{yval}', 
                   ha='center', va='center', color='black')

# Adicionar valores e percentuais dentro das barras de resolvidos
for i, bar in enumerate(resolved_bars):
    yval = bar.get_height()
    total_incidents = df_responsavel.values[i]  # Total de incidentes para o responsável atual

    # Calcular percentual apenas se houver incidentes resolvidos
    if yval > 0:
        percent = (yval / total_incidents) * 100
        # Colocar o valor e o percentual dentro da barra
        axs[1, 1].text(bar.get_x() + bar.get_width() / 2, yval / 2, f'{yval}\n({percent:.1f}%)', 
                       ha='center', va='center', color='black')

# Adicionar legenda ao gráfico
axs[1, 1].legend()  # Adicionar legenda apenas uma vez

# Ajustar espaçamento entre os gráficos e o título global
plt.subplots_adjust(wspace=0.4, hspace=0.5)  # Ajustar espaçamento horizontal e vertical
plt.tight_layout(rect=[0, 0, 1, 0.95])  # Deixar espaço para o título global

# Salvar os gráficos em uma única página do PDF
pdf.savefig(fig)

# Fechar o PDF
pdf.close()

# Exibir o caminho do arquivo PDF gerado
print(f"PDF gerado em: {pdf_path}")

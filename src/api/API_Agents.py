import requests
import pandas as pd
import warnings
import base64

# Suprime warnings de HTTPS inseguro
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# Configurações
API_KEY = 'ORINiDJqG-g0resN9EER'
DOMAIN = 'duasrodas'

# Autenticação Basic
auth_string = f"{API_KEY}:X"
auth_bytes = auth_string.encode('utf-8')
auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
HEADERS = {
    'Authorization': f'Basic {auth_base64}',
    'Content-Type': 'application/json'
}

# Configuração do pandas para mostrar tudo no terminal
pd.set_option('display.max_columns', None)   # Mostra todas as colunas
pd.set_option('display.max_rows', None)      # Mostra todas as linhas
pd.set_option('display.width', 200)          # Largura do terminal
pd.set_option('display.max_colwidth', None)  # Não corta o conteúdo das colunas

def get_agents():
    """
    Busca todos os agentes do Freshservice com os campos suportados.
    """
    agents = []
    page = 1
    while True:
        url = f"https://{DOMAIN}.freshservice.com/api/v2/agents?per_page=100&page={page}"
        response = requests.get(url, headers=HEADERS, verify=False)
        
        if response.status_code != 200:
            print(f"Erro ao buscar agentes: {response.status_code} - {response.text}")
            break
        
        data = response.json().get('agents', [])
        if not data:
            break
        
        for a in data:
            agents.append({
                'id': a.get('id'),
                'primeiro_nome': a.get('first_name'),
                'sobrenome': a.get('last_name'),
                'email': a.get('email'),              
                'cargo': a.get('job_title'),
                'ultimo_login_em': a.get('last_login_at'),
                'ultima_atividade_em': a.get('last_active_at')
            })
        page += 1

    return agents

if __name__ == "__main__":
    agentes = get_agents()
    df_agents = pd.DataFrame(agentes)

    # Mostra no terminal todos os agentes completos
    print(f"✅ {len(df_agents)} agentes carregados:\n")
    print(df_agents)

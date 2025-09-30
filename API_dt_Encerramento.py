import requests
import pandas as pd
import warnings
import base64

# -----------------------------
# Configurações
# -----------------------------
API_KEY = 'ORINiDJqG-g0resN9EER'  # Sua chave API Freshservice
DOMAIN = 'duasrodas'              # Subdomínio Freshservice

# Suprime warnings de SSL (não recomendado em produção)
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# Autenticação Basic
auth_string = f"{API_KEY}:X"
auth_bytes = auth_string.encode('utf-8')
auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
HEADERS = {
    'Authorization': f'Basic {auth_base64}',
    'Content-Type': 'application/json'
}

# -----------------------------
# Funções
# -----------------------------
def get_agents():
    """Busca todos os agentes com informações principais"""
    agents = []
    page = 1
    while True:
        url = f'https://{DOMAIN}.freshservice.com/api/v2/agents?per_page=100&page={page}'
        response = requests.get(url, headers=HEADERS, verify=False)
        if response.status_code != 200:
            print(f"Erro ao buscar agentes: {response.status_code}")
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
                'ocasional': a.get('occasional'),
                'cargo': a.get('job_title'),
                'ativo': a.get('active'),
                'ultimo_login_em': a.get('last_login_at'),
                'ultima_atividade_em': a.get('last_activity_at')
            })
        page += 1
    return agents

def get_tickets(limit=50):
    """Busca tickets limitados com responder_id e data de encerramento"""
    tickets = []
    page = 1
    total = 0
    while total < limit:
        url = f'https://{DOMAIN}.freshservice.com/api/v2/tickets?per_page=100&page={page}'
        response = requests.get(url, headers=HEADERS, verify=False)
        if response.status_code != 200:
            print(f"Erro ao buscar tickets na página {page}: {response.status_code}")
            break
        data = response.json().get('tickets', [])
        if not data:
            break
        for t in data:
            tickets.append({
                'id': t.get('id'),
                'assunto': t.get('subject'),
                'responder_id': t.get('responder_id'),
                'status': t.get('status'),
                'prioridade': t.get('priority'),
                'criacao': t.get('created_at'),
                'atualizacao': t.get('updated_at'),
                'encerramento': t.get('closed_at'),
                'solicitante_id': t.get('requester_id')
            })
            total += 1
            if total >= limit:
                break
        page += 1
    return tickets

# -----------------------------
# Execução Principal
# -----------------------------
if __name__ == "__main__":
    # Busca agentes
    agents = get_agents()
    if agents:
        df_agents = pd.DataFrame(agents)
        print(f"✅ {len(df_agents)} agentes carregados:\n")
        print(df_agents.to_string(index=False))
    else:
        print("⚠️ Nenhum agente encontrado.")

    # Mapeamento de responder_id → nome completo
    agent_map = {a['id']: f"{a['primeiro_nome']} {a['sobrenome']}" for a in agents}

    # Busca tickets
    tickets = get_tickets(limit=50)
    if tickets:
        for t in tickets:
            responder_id = t['responder_id']
            t['responder_nome'] = agent_map.get(responder_id, 'Desconhecido')
        df_tickets = pd.DataFrame(tickets)
        print(f"\n✅ {len(df_tickets)} tickets carregados com data de encerramento:\n")
        print(df_tickets.to_string(index=False))
    else:
        print("\n⚠️ Nenhum ticket encontrado.")

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
                'cargo': a.get('job_title'),
                'ativo': a.get('active')
            })
        page += 1
    return agents

def get_tickets(limit=50):
    """Busca tickets limitados com todos os campos principais"""
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
                #'descricao': t.get('description_text'),
                #'status': t.get('status'),
                #'prioridade': t.get('priority'),
                #'tipo': t.get('type'),
                'responder_id': t.get('responder_id'),
                'requester_id': t.get('requester_id'),
                #'email': t.get('email'),
                #'nome': t.get('name'),
                #'telefone': t.get('phone'),
                'criado_em': t.get('created_at'),
                'atualizado_em': t.get('updated_at'),
                #'urgencia': t.get('urgency'),
                #'impacto': t.get('impact'),
                #'categoria': t.get('category'),
                #'subcategoria': t.get('subcategory'),
                #'categoria_item': t.get('item_category'),
                #'notas_de_resolucao': t.get('resolution_notes'),
                #'notas_de_resolucao_html': t.get('resolution_html_notes')
            })
            total += 1
            if total >= limit:
                break
        page += 1
    return tickets

if __name__ == "__main__":
    # Busca agentes e cria mapeamento responder_id -> nome
    agents = get_agents()
    agent_map = {a['id']: f"{a['primeiro_nome']} {a['sobrenome']}" for a in agents}

    # Busca tickets
    tickets = get_tickets(limit=10)
    for t in tickets:
        responder_id = t['responder_id']
        t['responder_nome'] = agent_map.get(responder_id, 'Desconhecido')

    # Exibe todos os tickets no terminal
    df_tickets = pd.DataFrame(tickets)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 200)
    print(f"✅ {len(df_tickets)} tickets carregados:\n")
    print(df_tickets)

import requests
import pandas as pd
import warnings
import base64
from datetime import datetime, timedelta
import urllib.parse

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

def get_tickets_with_filters(query=None, limit=100):
    """
    Busca tickets com filtros usando a API de filtros do Freshservice
    
    Args:
        query (str): Query de filtro no formato Freshservice
        limit (int): Limite de tickets a buscar
    
    Returns:
        list: Lista de tickets filtrados
    """
    tickets = []
    page = 1
    total = 0
    
    while total < limit:
        if query:
            # URL encode da query
            encoded_query = urllib.parse.quote(query)
            url = f'https://{DOMAIN}.freshservice.com/api/v2/tickets/filter?query={encoded_query}&per_page=30&page={page}'
        else:
            url = f'https://{DOMAIN}.freshservice.com/api/v2/tickets?per_page=30&page={page}'
        
        response = requests.get(url, headers=HEADERS, verify=False)
        
        if response.status_code != 200:
            print(f"Erro ao buscar tickets na página {page}: {response.status_code}")
            print(f"Resposta: {response.text}")
            break
            
        data = response.json().get('tickets', [])
        if not data:
            break
            
        for t in data:
            tickets.append({
                'id': t.get('id'),
                'assunto': t.get('subject'),
                'descricao': t.get('description_text'),
                'status': t.get('status'),
                'prioridade': t.get('priority'),
                'tipo': t.get('type'),
                'responder_id': t.get('responder_id'),
                'requester_id': t.get('requester_id'),
                'email': t.get('email'),
                'nome': t.get('name'),
                'telefone': t.get('phone'),
                'criado_em': t.get('created_at'),
                'atualizado_em': t.get('updated_at'),
                'data_vencimento': t.get('due_by'),
                'primeira_resposta_vencimento': t.get('fr_due_by'),
                'urgencia': t.get('urgency'),
                'impacto': t.get('impact'),
                'categoria': t.get('category'),
                'subcategoria': t.get('subcategory'),
                'categoria_item': t.get('item_category'),
                'notas_de_resolucao': t.get('resolution_notes'),
                'notas_de_resolucao_html': t.get('resolution_html_notes'),
                'data_encerramento': t.get('closed_at'),  # Campo de data de encerramento
                'resolvido_em': t.get('resolved_at'),     # Campo de data de resolução
                'grupo_id': t.get('group_id'),
                'tags': t.get('tags')
            })
            total += 1
            if total >= limit:
                break
        page += 1
    
    return tickets

def get_closed_tickets(data_inicio=None, data_fim=None, limit=100):
    """
    Busca tickets encerrados em um período específico
    
    Args:
        data_inicio (str): Data início no formato 'YYYY-MM-DD'
        data_fim (str): Data fim no formato 'YYYY-MM-DD'
        limit (int): Limite de tickets
    
    Returns:
        list: Lista de tickets encerrados
    """
    # Status 5 = Closed (encerrado)
    query_parts = ["status:5"]
    
    if data_inicio:
        query_parts.append(f"updated_at:>'{data_inicio}'")
    
    if data_fim:
        query_parts.append(f"updated_at:<'{data_fim}'")
    
    query = " AND ".join(query_parts)
    
    print(f"Query utilizada: {query}")
    return get_tickets_with_filters(query, limit)

def get_resolved_tickets(data_inicio=None, data_fim=None, limit=100):
    """
    Busca tickets resolvidos em um período específico
    
    Args:
        data_inicio (str): Data início no formato 'YYYY-MM-DD'
        data_fim (str): Data fim no formato 'YYYY-MM-DD'
        limit (int): Limite de tickets
    
    Returns:
        list: Lista de tickets resolvidos
    """
    # Status 4 = Resolved (resolvido)
    query_parts = ["status:4"]
    
    if data_inicio:
        query_parts.append(f"updated_at:>'{data_inicio}'")
    
    if data_fim:
        query_parts.append(f"updated_at:<'{data_fim}'")
    
    query = " AND ".join(query_parts)
    
    print(f"Query utilizada: {query}")
    return get_tickets_with_filters(query, limit)

def get_tickets_by_priority(prioridade, limit=50):
    """
    Busca tickets por prioridade
    
    Args:
        prioridade (int): 1=Baixa, 2=Média, 3=Alta, 4=Urgente
        limit (int): Limite de tickets
    
    Returns:
        list: Lista de tickets da prioridade especificada
    """
    query = f"priority:{prioridade}"
    return get_tickets_with_filters(query, limit)

def get_tickets_by_agent(agent_id, limit=50):
    """
    Busca tickets atribuídos a um agente específico
    
    Args:
        agent_id (int): ID do agente
        limit (int): Limite de tickets
    
    Returns:
        list: Lista de tickets do agente
    """
    query = f"agent_id:{agent_id}"
    return get_tickets_with_filters(query, limit)

def format_ticket_data(tickets, agents_map):
    """
    Formata os dados dos tickets adicionando nomes dos agentes
    
    Args:
        tickets (list): Lista de tickets
        agents_map (dict): Mapeamento de ID para nome dos agentes
    
    Returns:
        pd.DataFrame: DataFrame formatado
    """
    for ticket in tickets:
        responder_id = ticket.get('responder_id')
        ticket['responder_nome'] = agents_map.get(responder_id, 'Não atribuído')
        
        # Formatar datas para melhor visualização
        for date_field in ['criado_em', 'atualizado_em', 'data_encerramento', 'resolvido_em']:
            if ticket.get(date_field):
                try:
                    date_obj = datetime.fromisoformat(ticket[date_field].replace('Z', '+00:00'))
                    ticket[f'{date_field}_formatado'] = date_obj.strftime('%d/%m/%Y %H:%M')
                except:
                    ticket[f'{date_field}_formatado'] = ticket[date_field]
    
    return pd.DataFrame(tickets)

if __name__ == "__main__":
    print("🔍 Testando API de Tickets com Filtros\n")
    
    # Busca agentes e cria mapeamento
    print("📋 Buscando agentes...")
    agents = get_agents()
    agent_map = {a['id']: f"{a['primeiro_nome']} {a['sobrenome']}" for a in agents}
    print(f"✅ {len(agents)} agentes carregados\n")
    
    # Exemplo 1: Tickets encerrados nos últimos 7 dias
    print("🎯 Exemplo 1: Tickets encerrados nos últimos 7 dias")
    data_fim = datetime.now().strftime('%Y-%m-%d')
    data_inicio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    tickets_encerrados = get_closed_tickets(data_inicio, data_fim, limit=10)
    if tickets_encerrados:
        df_encerrados = format_ticket_data(tickets_encerrados, agent_map)
        print(f"✅ {len(df_encerrados)} tickets encerrados encontrados:")
        print(df_encerrados[['id', 'assunto', 'status', 'responder_nome', 'data_encerramento_formatado']].head())
    else:
        print("❌ Nenhum ticket encerrado encontrado no período")
    
    print("\n" + "="*80 + "\n")
    
    # Exemplo 2: Tickets de alta prioridade
    print("🚨 Exemplo 2: Tickets de alta prioridade")
    tickets_alta_prioridade = get_tickets_by_priority(3, limit=5)
    if tickets_alta_prioridade:
        df_alta = format_ticket_data(tickets_alta_prioridade, agent_map)
        print(f"✅ {len(df_alta)} tickets de alta prioridade encontrados:")
        print(df_alta[['id', 'assunto', 'prioridade', 'status', 'responder_nome']].head())
    else:
        print("❌ Nenhum ticket de alta prioridade encontrado")
    
    print("\n" + "="*80 + "\n")
    
    # Exemplo 3: Query personalizada
    print("🔧 Exemplo 3: Query personalizada - Tickets resolvidos OU encerrados")
    query_personalizada = "(status:4 OR status:5)"
    tickets_personalizados = get_tickets_with_filters(query_personalizada, limit=5)
    if tickets_personalizados:
        df_personalizados = format_ticket_data(tickets_personalizados, agent_map)
        print(f"✅ {len(df_personalizados)} tickets encontrados:")
        print(df_personalizados[['id', 'assunto', 'status', 'responder_nome', 'atualizado_em_formatado']].head())
    else:
        print("❌ Nenhum ticket encontrado com a query personalizada")
import requests
import pandas as pd
import warnings
import base64
from datetime import datetime, date, timezone, timedelta
import urllib.parse

# Suprime warnings de HTTPS inseguro
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# Configurações
API_KEY = 'ORINiDJqG-g0resN9EER'
DOMAIN = 'duasrodas'

# Fuso horário do Brasil (UTC-3)
BRAZIL_TZ = timezone(timedelta(hours=-3))

# Autenticação Basic
auth_string = f"{API_KEY}:X"
auth_bytes = auth_string.encode('utf-8')
auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
HEADERS = {
    'Authorization': f'Basic {auth_base64}',
    'Content-Type': 'application/json'
}

def get_groups():
    """Busca todos os grupos de agentes"""
    groups = []
    page = 1
    while True:
        url = f'https://{DOMAIN}.freshservice.com/api/v2/groups?per_page=100&page={page}'
        response = requests.get(url, headers=HEADERS, verify=False)
        if response.status_code != 200:
            print(f"Erro ao buscar grupos: {response.status_code}")
            break
        data = response.json().get('groups', [])
        if not data:
            break
        for g in data:
            groups.append({
                'id': g.get('id'),
                'nome': g.get('name'),
                'descricao': g.get('description'),
                'tipo': g.get('type'),
                'ativo': g.get('active')
            })
        page += 1
    return groups

def get_agents():
    """Busca todos os agentes com informações principais incluindo grupos"""
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
            # Extrai os IDs dos grupos que o agente pertence
            group_ids = []
            if a.get('member_of'):
                group_ids.extend(a.get('member_of', []))
            if a.get('observer_of'):
                group_ids.extend(a.get('observer_of', []))
            
            agents.append({
                'id': a.get('id'),
                'primeiro_nome': a.get('first_name'),
                'sobrenome': a.get('last_name'),
                'email': a.get('email'),
                'cargo': a.get('job_title'),
                'ativo': a.get('active'),
                'group_ids': list(set(group_ids))  # Remove duplicatas
            })
        page += 1
    return agents

def get_all_tickets_with_due_dates():
    """Busca todos os tickets que têm data de vencimento de resolução"""
    tickets = []
    page = 1
    
    print("🔍 Buscando todos os tickets com data de vencimento...")
    
    while True:
        # Busca tickets que não estão resolvidos nem fechados
        url = f'https://{DOMAIN}.freshservice.com/api/v2/tickets?per_page=100&page={page}'
        
        response = requests.get(url, headers=HEADERS, verify=False)
        
        if response.status_code != 200:
            print(f"Erro ao buscar tickets na página {page}: {response.status_code}")
            break
            
        data = response.json().get('tickets', [])
        if not data:
            break
            
        for t in data:
            # Só adiciona tickets que têm data de vencimento de resolução E não estão resolvidos/fechados
            if t.get('due_by') and t.get('status') not in [4, 5]:
                tickets.append({
                    'id': t.get('id'),
                    'assunto': t.get('subject'),
                    'descricao': t.get('description_text'),
                    'status': t.get('status'),
                    'status_nome': get_status_name(t.get('status')),
                    'prioridade': t.get('priority'),
                    'prioridade_nome': get_priority_name(t.get('priority')),
                    'tipo': t.get('type'),
                    'responder_id': t.get('responder_id'),
                    'requester_id': t.get('requester_id'),
                    'email': t.get('email'),
                    'nome': t.get('name'),
                    'telefone': t.get('phone'),
                    'criado_em': t.get('created_at'),
                    'atualizado_em': t.get('updated_at'),
                    'data_vencimento_resolucao': t.get('due_by'),
                    'data_vencimento_primeira_resposta': t.get('fr_due_by'),
                    'resolvido_em': t.get('resolved_at'),
                    'fechado_em': t.get('closed_at'),
                    'urgencia': t.get('urgency'),
                    'impacto': t.get('impact'),
                    'categoria': t.get('category'),
                    'subcategoria': t.get('subcategory'),
                    'categoria_item': t.get('item_category'),
                    'grupo_id': t.get('group_id'),
                    'tags': t.get('tags'),
                    'notas_de_resolucao': t.get('resolution_notes')
                })
        
        page += 1
        
        # Limita para não sobrecarregar - ajuste conforme necessário
        if len(tickets) >= 2000:
            break
    
    return tickets

def filter_overdue_resolution_tickets(tickets):
    """Filtra tickets que venceram a resolução (considerando data E hora no fuso horário brasileiro)"""
    overdue_tickets = []
    # Hora atual no fuso horário brasileiro
    now = datetime.now(BRAZIL_TZ)
    
    print(f"📅 Data/hora atual (Brasil): {now.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🔍 Analisando {len(tickets)} tickets com data de vencimento...")
    
    for ticket in tickets:
        due_by = ticket.get('data_vencimento_resolucao')
        status = ticket.get('status')
        
        if due_by:
            try:
                # Converte a data de vencimento de UTC para horário brasileiro
                due_date_utc = datetime.fromisoformat(due_by.replace('Z', '+00:00'))
                due_date_brazil = due_date_utc.astimezone(BRAZIL_TZ)
                
                # Se a data/hora atual é maior que a data/hora de vencimento, está vencido
                if now > due_date_brazil:
                    # Calcula quantos dias e horas está vencido
                    time_diff = now - due_date_brazil
                    days_overdue = time_diff.days
                    hours_overdue = time_diff.seconds // 3600
                    
                    ticket['dias_vencido'] = days_overdue
                    ticket['horas_vencido'] = hours_overdue
                    ticket['data_vencimento_formatada'] = due_date_brazil.strftime('%d/%m/%Y %H:%M')
                    ticket['tempo_vencido_texto'] = f"{days_overdue}d {hours_overdue}h"
                    
                    overdue_tickets.append(ticket)
                    
            except Exception as e:
                print(f"Erro ao processar ticket {ticket.get('id')}: {e}")
                continue
    
    return overdue_tickets

def get_status_name(status_code):
    """Converte código de status para nome"""
    status_map = {
        2: 'Aberto', 3: 'Pendente', 4: 'Resolvido', 
        5: 'Fechado', 6: 'Aguardando Cliente', 7: 'Aguardando Terceiros'
    }
    return status_map.get(status_code, f'Status {status_code}')

def get_priority_name(priority_code):
    """Converte código de prioridade para nome"""
    priority_map = {
        1: 'Baixa', 2: 'Média', 3: 'Alta', 4: 'Urgente'
    }
    return priority_map.get(priority_code, f'Prioridade {priority_code}')


if __name__ == "__main__":
    print("🔍 Buscando Tickets Vencidos para Resolução (Data + Hora)\n")
    
    # Busca grupos primeiro
    print("👥 Buscando grupos...")
    groups = get_groups()
    group_map = {g['id']: g['nome'] for g in groups}
    print(f"✅ {len(groups)} grupos carregados\n")
    
    # Busca agentes
    print("📋 Buscando agentes...")
    agents = get_agents()
    agent_map = {a['id']: f"{a['primeiro_nome']} {a['sobrenome']}" for a in agents}
    agent_group_map = {a['id']: a['group_ids'] for a in agents}
    print(f"✅ {len(agents)} agentes carregados\n")
    
    # Busca tickets
    print("🎫 Buscando tickets com data de vencimento...")
    all_tickets = get_all_tickets_with_due_dates()
    print(f"✅ {len(all_tickets)} tickets com data de vencimento carregados\n")
    
    # Adiciona informações do responsável e grupos aos tickets
    for ticket in all_tickets:
        responder_id = ticket['responder_id']
        ticket['responder_nome'] = agent_map.get(responder_id, 'Não atribuído')
        
        # Adiciona informações dos grupos do responsável
        responder_groups = agent_group_map.get(responder_id, [])
        group_names = [group_map.get(gid, f'Grupo {gid}') for gid in responder_groups]
        ticket['responder_grupos'] = ', '.join(group_names) if group_names else 'Sem grupo'
    
    # Filtra tickets vencidos na resolução
    print("⏰ Filtrando tickets vencidos na resolução...")
    overdue_tickets = filter_overdue_resolution_tickets(all_tickets)
    
    if overdue_tickets:
        print(f"🚨 {len(overdue_tickets)} tickets vencidos na resolução encontrados:\n")
        
        # Cria DataFrame para melhor visualização
        df_overdue = pd.DataFrame(overdue_tickets)
        
        # Colunas para exibir no terminal (ocultando assunto, status_nome e prioridade_nome)
        columns_to_show = [
            'id', 
            'responder_nome', 'responder_grupos', 'data_vencimento_formatada', 'tempo_vencido_texto'
        ]
        
        # Configurações de exibição do pandas
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 400)
        pd.set_option('display.max_colwidth', 50)
        
        # Ordena por dias vencido (mais vencido primeiro)
        df_sorted = df_overdue.sort_values(['dias_vencido', 'horas_vencido'], ascending=[False, False])
        print(df_sorted[columns_to_show])  # Mostra apenas as colunas selecionadas no terminal
        
        # Salva em Excel com tratamento de erro (salva TODAS as colunas)
        try:
            df_overdue.to_excel('tickets_vencidos_resolucao.xlsx', index=False)
            print(f"\n💾 Dados salvos em: tickets_vencidos_resolucao.xlsx")
        except PermissionError:
            # Tenta salvar com um nome alternativo se o arquivo estiver aberto
            import time
            timestamp = int(time.time())
            filename = f'tickets_vencidos_resolucao_{timestamp}.xlsx'
            df_overdue.to_excel(filename, index=False)
            print(f"\n💾 Arquivo original estava em uso. Dados salvos em: {filename}")
            print(f"⚠️  Feche o arquivo Excel e execute novamente para sobrescrever o arquivo original.")
        except Exception as e:
            print(f"\n❌ Erro ao salvar arquivo Excel: {e}")
        
    else:
        print("✅ Nenhum ticket vencido na resolução encontrado")

    print(f"\n🎯 Resumo:")
    print(f"📊 Total de tickets com data de vencimento: {len(all_tickets)}")
    print(f"⏰ Tickets vencidos na resolução: {len(overdue_tickets)}")
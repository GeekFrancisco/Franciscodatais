import requests
import base64
import pandas as pd

dominio = "duasrodas.freshservice.com"
api_key = "Jvxk1AxTK4SQCj1aHrSv"

auth_string = f"{api_key}:X"
auth_bytes = auth_string.encode('utf-8')
auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')

headers = {
    "Authorization": f"Basic {auth_base64}",
    "Content-Type": "application/json"
}

source_map = {
    1: "Email",
    2: "Portal",
    3: "Telefone",
    4: "Chat",
    9: "Automação",
    12: "Integração"
}

status_map = {
    2: "Aberto",
    3: "Em andamento",
    4: "Aguardando",
    5: "Fechado"
}

priority_map = {
    1: "Baixa",
    2: "Média",
    3: "Alta",
    4: "Urgente"
}

cache_users = {}
def get_user_name(user_id):
    if user_id is None:
        return "Não atribuído"
    if user_id in cache_users:
        return cache_users[user_id]
    url = f"https://{dominio}/api/v2/users/{user_id}"
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        json_data = r.json()
        # Ajuste aqui conforme estrutura real da API
        name = json_data.get("user", {}).get("name")
        if not name:
            # Se não achar, debug: imprime json para ver o que retorna
            print(f"Resposta inesperada para usuário {user_id}:", json_data)
            name = "Desconhecido"
    else:
        print(f"Erro ao buscar usuário {user_id}: {r.status_code} - {r.text}")
        name = "Desconhecido"
    cache_users[user_id] = name
    return name

cache_departments = {}
def get_department_name(department_id):
    if department_id is None:
        return ""
    if department_id in cache_departments:
        return cache_departments[department_id]
    url = f"https://{dominio}/api/v2/departments/{department_id}"
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        json_data = r.json()
        name = json_data.get("department", {}).get("name")
        if not name:
            print(f"Resposta inesperada para departamento {department_id}:", json_data)
            name = ""
    else:
        print(f"Erro ao buscar departamento {department_id}: {r.status_code} - {r.text}")
        name = ""
    cache_departments[department_id] = name
    return name

url_tickets = f"https://{dominio}/api/v2/tickets"
response = requests.get(url_tickets, headers=headers)

if response.status_code == 200:
    dados = response.json()
    tickets = dados.get("tickets", [])

    tabela = []
    
    for ticket in tickets:
        departamento_nome = get_department_name(ticket.get("department_id"))
        solicitante_nome = get_user_name(ticket["requester_id"])  # tentar pelo usuário mesmo
        responsavel_nome = get_user_name(ticket.get("responder_id"))

        tabela.append({
            "ID": ticket["id"],
            "Assunto": ticket["subject"],
            "Fonte": source_map.get(ticket.get("source"), "Desconhecida"),
            "Status": status_map.get(ticket.get("status"), "Desconhecido"),
            "Prioridade": priority_map.get(ticket.get("priority"), "Desconhecida"),
            "Criado em": ticket.get("created_at", ""),
            "Descrição": ticket.get("description_text", ""),
            "Tipo": ticket.get("type", ""),
            "Categoria": ticket.get("category", ""),
            "Subcategoria": ticket.get("sub_category", ""),
            "Departamento": departamento_nome,
            "Solicitante": solicitante_nome,
            "Responsável": responsavel_nome,
            "Atualizado em": ticket.get("updated_at", ""),
        })

    df = pd.DataFrame(tabela)
    print(df)
    df.to_excel("tickets.xlsx", index=False)
    print("Arquivo 'tickets.xlsx' salvo com sucesso!")

else:
    print(f"Erro ao buscar tickets: {response.status_code}")
    print(response.text)

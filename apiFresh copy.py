import requests
import base64
import json

# --- CONFIGURAÇÕES ---
dominio = "duasrodas.freshservice.com"
api_key = "FEK27PwIV124VdpScNzQ"

auth_string = f"{api_key}:X"
auth_bytes = auth_string.encode('utf-8')
auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')

headers = {
    "Authorization": f"Basic {auth_base64}",
    "Content-Type": "application/json"
}

url = f"https://{dominio}/api/v2/ticket_fields"

response = requests.get(url, headers=headers)

if response.status_code == 200:
    dados = response.json()
    campos = dados.get("ticket_fields", [])
    print(f"Total de campos: {len(campos)}")
    for campo in campos:
        print(f"ID: {campo.get('id')} - Label: {campo.get('label')} - Tipo: {campo.get('field_type')} - Obrigatório: {campo.get('required')}")
else:
    print(f"Erro ao buscar campos: {response.status_code}")
    print(response.text)

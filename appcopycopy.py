import requests
import json

# Definindo os parâmetros de autenticação
tokenAPI = "live_7a035526eff1aa818cb06a5da37ae6cad6e85fa8f394e36461094939f26a19cb"
cryptKey = "live_crypt_fbEkhz3AvSU2lZCwaBVgSp9usYCuAzWj"

# Endpoint da API para listar os documentos
url_documents = "https://secure.d4sign.com.br/api/v1/documents"

# Parâmetros de autenticação
params = {'tokenAPI': tokenAPI, 'cryptKey': cryptKey}

# Cabeçalhos da requisição
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

try:
    # Fazendo a requisição GET para listar documentos
    response = requests.get(url_documents, headers=headers, params=params)

    # Verificando se a resposta foi bem-sucedida
    if response.status_code == 200:
        documents = response.json()

        # Verificando se os documentos foram retornados corretamente
        if isinstance(documents, list) and len(documents) > 0:
            formatted_documents = []

            for doc in documents:
                uuid_document = doc.get("uuidDoc", "Não informado")

                # Endpoint para obter os signatários do documento
                url_signers = f"https://secure.d4sign.com.br/api/v1/documents/{uuid_document}/list"
                response_signers = requests.get(url_signers, headers=headers, params=params)

                if response_signers.status_code == 200:
                    signers = response_signers.json()
                    print(f"Signatários para {uuid_document}: {json.dumps(signers, indent=4, ensure_ascii=False)}")
                else:
                    print(f"Erro ao obter signatários para {uuid_document}: {response_signers.status_code}")
                    print(response_signers.text)
                    signers = []

                formatted_signers = [
                    {
                        "ID_Signatário": signer.get("uuid", "Não informado"),
                        "Nome_Signatário": signer.get("name", "Não informado"),
                        "Email_Signatário": signer.get("email", "Não informado"),
                        "Status_Assinatura": signer.get("status", "Não informado"),
                        "Data_Assinatura": signer.get("signedDate", "Não assinado")
                    }
                    for signer in signers
                ]

                formatted_documents.append({
                    "ID_Documento": uuid_document,
                    "Nome_Documento": doc.get("nameDoc", "Não informado"),
                    "Tipo_Documento": doc.get("type", "Não informado"),
                    "Tamanho_Bytes": doc.get("size", "Não informado"),
                    "Quantidade_Páginas": doc.get("pages", "Não informado"),
                    "ID_Cofre": doc.get("uuidSafe", "Não informado"),
                    "Nome_Cofre": doc.get("safeName", "Não informado"),
                    "ID_Status": doc.get("statusId", "Não informado"),
                    "Descrição_Status": doc.get("statusName", "Não informado"),
                    "Comentário_Status": doc.get("statusComment", "Sem comentários"),
                    "Cancelado_Por": doc.get("whoCanceled", "Não cancelado"),
                    "Signatários": formatted_signers
                })

            # Exibindo os documentos formatados com signatários
            print("Documentos encontrados com signatários:")
            print(json.dumps(formatted_documents, indent=4, ensure_ascii=False))
        else:
            print("Nenhum documento foi encontrado ou o formato da resposta é inesperado.")

    else:
        print(f"Erro na requisição: {response.status_code}")
        print(response.text)

except requests.exceptions.RequestException as e:
    print(f"Ocorreu um erro na requisição: {e}")

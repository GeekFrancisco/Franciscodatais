import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

# Escopos necessários para acessar a conta do YouTube
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

def main():
    # Desabilitar verificação de HTTPS para testes locais
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    client_secrets_file = "client_secrets.json"

    if not os.path.exists(client_secrets_file):
        search_dirs = [".", "secrets"]
        candidates = []
        for d in search_dirs:
            if os.path.isdir(d):
                for name in os.listdir(d):
                    if name.lower().endswith(".json") and "client" in name.lower():
                        candidates.append(os.path.join(d, name))
        if candidates:
            client_secrets_file = candidates[0]
        else:
            print("ERRO: Nenhum arquivo de credenciais foi encontrado.")
            print("Coloque o JSON baixado do Google na pasta do projeto e rode novamente.")
            return

    try:
        # Iniciar o fluxo de autenticação
        print("Iniciando processo de autenticação...")
        print("Uma janela do navegador será aberta. Por favor, faça login.")
        print("IMPORTANTE: Se você tem múltiplos canais, escolha a conta/canal que deseja verificar nesta tela.")
        
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, SCOPES
        )
        credentials = flow.run_local_server(port=0)
        
        # Construir o serviço da API do YouTube
        youtube = googleapiclient.discovery.build(
            "youtube", "v3", credentials=credentials
        )

        # Solicitar informações do canal autenticado
        print("\nConsultando informações do canal...")
        request = youtube.channels().list(
            part="snippet,id,statistics",
            mine=True
        )
        response = request.execute()

        if "items" in response and len(response["items"]) > 0:
            print("\n" + "="*50)
            print("CANAIS DISPONÍVEIS (Baseado na sua escolha de login)")
            print("="*50)
            for item in response["items"]:
                channel_id = item["id"]
                title = item["snippet"]["title"]
                description = item["snippet"]["description"][:100].replace("\n", " ") + "..."
                subs = item["statistics"].get("subscriberCount", "N/A")
                video_count = item["statistics"].get("videoCount", "N/A")
                
                print(f"Nome do Canal: {title}")
                print(f"ID do Canal:   {channel_id}")
                print(f"Inscritos:     {subs}")
                print(f"Vídeos:        {video_count}")
                print(f"Descrição:     {description}")
                print("-" * 50)
            
            print("\nNOTA: Para ver outro canal, execute este script novamente e escolha outra conta/marca na tela de login do Google.")
            print("="*50)
        else:
            print("Nenhum canal encontrado para a conta autenticada.")

    except Exception as e:
        print(f"\nOcorreu um erro: {str(e)}")

if __name__ == "__main__":
    main()

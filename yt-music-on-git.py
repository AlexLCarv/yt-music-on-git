import os
import json
from flask import Flask
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

app = Flask(__name__)

def authenticate():
    """Autentica o usuário e renova o token, se necessário."""
    token_json = os.getenv("TOKEN_JSON")  # Pega o token do ambiente
    credentials_json = os.getenv("CREDENTIALS_JSON")  # Credenciais do Google
    
    creds = None

    # ✅ Se já existe um token salvo, usa ele
    if token_json:
        creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)

    # 🔄 Se o token expirou, tenta renovar
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # Renova o token automaticamente
            os.environ["TOKEN_JSON"] = creds.to_json()  # Atualiza a variável de ambiente
        else:
            # 🚀 Primeira autenticação: usuário precisa logar manualmente
            if not credentials_json:
                raise ValueError("Credenciais não encontradas!")

            with open("credentials_temp.json", "w") as temp_file:
                temp_file.write(credentials_json)

            flow = InstalledAppFlow.from_client_secrets_file("credentials_temp.json", SCOPES)
            creds = flow.run_local_server(port=8080)

            os.remove("credentials_temp.json")  # Remove o arquivo temporário

        # 🔐 Salva o token atualizado no ambiente
        os.environ["TOKEN_JSON"] = creds.to_json()

    return creds

def get_last_activity():
    """Obtém o último vídeo curtido do usuário no YouTube e exibe com miniatura e título à direita."""
    creds = authenticate()
    youtube = build("youtube", "v3", credentials=creds)

    response = youtube.videos().list(
        part="snippet",
        myRating="like",
        maxResults=1  # Apenas 1 vídeo
    ).execute()

    if "items" in response and response["items"]:
        item = response["items"][0]
        snippet = item["snippet"]
        if len(snippet.get("tags", [])) > 2:
            title = snippet.get("tags")[2]
            album = snippet.get("tags")[1]
        else:
            title = snippet.get("tags")[1]
            album = ''
        channel_title = snippet.get("tags")[0]
        video_id = item["id"]  # Pegando o ID correto do vídeo
        thumbnail_url = snippet["thumbnails"]["default"]["url"]

        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Layout semelhante ao Spotify (foto à esquerda, título à direita)
        html_content = f"""
        <div style="background-color: #fff; border-radius: 15px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); padding: 15px; margin: 20px 0; display: flex; align-items: center; max-width: 400px;">
            <img src="{thumbnail_url}" alt="Thumbnail" style="width: 60px; height: 60px; margin-right: 15px; border-radius: 10px;">
            <div style="display: flex; flex-direction: column; justify-content: center; flex-grow: 1; text-align: center;">
                <p style="margin: 0; font-size: 14px; color: #888;">{album}</p>
                <p style="margin: 5; font-size: 16px; font-weight: bold; color: #333;">
                    <a href="{video_url}" target="_blank" style="text-decoration: none; color: #333;">
                        {title}
                    </a>
                </p>
                <p style="margin: 0; font-size: 14px; color: #888;">{channel_title}</p> 
            </div>
        </div>
        """

        return html_content

    return "Nenhuma atividade encontrada."

@app.route("/")
def show_activity():
    """Endpoint para exibir a última atividade no YouTube."""
    return get_last_activity()

if __name__ == "__main__":
    app.run(port=8080, debug=True)

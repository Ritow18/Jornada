import os
from google import genai
from dotenv import load_dotenv

# 1. Carrega as variáveis de ambiente do arquivo .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
chat = client.chats.create(model='gemini-2.5-flash')

print("Inicio do Chat: \n" + "-"*50 + "\n")

while True:

    mensagem_usuario = input("")

    if mensagem_usuario.lower() == "sair":
        print('saindo...')
        break

    response = chat.send_message(mensagem_usuario)

    # 5. Imprime a resposta no terminal
    print(f"Bot IA: {response.text}")
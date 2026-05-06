import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("Buscando modelos disponíveis na sua conta...\n")

# Pede para a API listar todos os modelos que você tem acesso
for model in client.models.list():
    # Vamos filtrar para mostrar apenas os modelos que contêm "gemini" no nome
    if "gemini" in model.name:
        print(f"Nome aceito pela API: {model.name}")
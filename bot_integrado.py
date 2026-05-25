import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key = os.getenv("GEMINI_API_KEY"))

ARQUIVO_CACHE = "banco_local/cache_alarmes.json"

try:
    with open(ARQUIVO_CACHE,"r",encoding="utf-8") as f:
        alarmes_atuais = json.load(f)
        dados_para_ia = json.dumps(alarmes_atuais,indent=2,ensure_ascii=False)
except FileNotFoundError:
    dados_para_ia = "[]" #garante que se o arquivo não existir, ele não vai passar nada para a IA ao invés de dados antigos
    print("Aviso: Arquivo do cache não foi encontrado, ps: já rodou o código de busca na API? (vigia)")

# 4. Cria a "Personalidade" e injeta os dados na memória base da IA
instrucao_do_sistema = f"""
Você é o assistente virtual de suporte técnico da Eletrofrio Refrigeração.
Segue em seguida, os dados atuais do cache local em tempo real dos equipamentos, responda apenas com base neles, caso contrário
digaque não é possivel responder a pergunta do usuário:
{dados_para_ia}
"""

# 6. Inicia o Chat
chat = client.chats.create(
    model='gemini-2.5-flash',
    config=types.GenerateContentConfig(system_instruction=instrucao_do_sistema, temperature=0.2)
)

print("\n  Bot da Eletrofrio integrado e online! (Digite 'sair' para encerrar)")
print("-" * 60)

while True:
    mensagem_usuario = input("\nVocê: ")
    
    if mensagem_usuario.lower() == 'sair': break
    
    print("Pensando...")

    response = chat.send_message(mensagem_usuario)
    print(f"\nBot Eletrofrio: {response.text}\n")
    
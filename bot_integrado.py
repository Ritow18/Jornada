import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

# 1. Importa a sua função do outro arquivo! 
# (Isso só funciona se o eletrofrio_api.py estiver na mesma pasta)
from eletrofrio_api import buscar_alarmes

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("Buscando dados ao vivo da Eletrofrio...")
# 2. Pega os alarmes reais usando o código que você já fez
alarmes_atuais = buscar_alarmes() 

# 3. Transforma a lista de dados num formato de texto organizado para a IA ler
dados_para_ia = json.dumps(alarmes_atuais, indent=2, ensure_ascii=False)

# 4. Cria a "Personalidade" e injeta os dados na memória base da IA
instrucao_do_sistema = f"""
Você é o assistente virtual de suporte técnico da Eletrofrio Refrigeração.
Você é educado, prestativo e fala como um humano.

Abaixo estão os dados EM TEMPO REAL dos alarmes das câmaras frias dos nossos clientes.
Se o usuário perguntar sobre o status de alguma loja ou se há problemas, use EXCLUSIVAMENTE esses dados para responder. Não invente informações.

DADOS DOS ALARMES ATUAIS:
{dados_para_ia}
"""

# 5. Configura o chat com essa instrução e ajusta a 'temperatura'
# Temperatura baixa (0.2) deixa a IA mais séria e focada nos dados (ótimo para bots de empresas)
configuracao = types.GenerateContentConfig(
    system_instruction=instrucao_do_sistema,
    temperature=0.2 
)

# 6. Inicia o Chat
chat = client.chats.create(
    model='gemini-2.5-flash',
    config=configuracao
)

print("\n❄️  Bot da Eletrofrio integrado e online! (Digite 'sair' para encerrar)")
print("-" * 60)

while True:
    mensagem_usuario = input("\nVocê: ")
    
    if mensagem_usuario.lower() == 'sair':
        print("Encerrando o sistema...")
        break
    
    print("Pensando...")
    response = chat.send_message(mensagem_usuario)
    
    print(f"\nBot Eletrofrio: {response.text}")
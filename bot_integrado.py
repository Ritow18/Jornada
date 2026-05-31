import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
ARQUIVO_CACHE = "banco_local/cache_alarmes.json"

def consultar_ia(mensagem_usuario, numero_cliente):
    print(f"\n[BOT] Iniciando consulta. Mensagem recebida: '{mensagem_usuario}'")

    # 1. LÊ O ARQUIVO SEMPRE QUE UMA MENSAGEM CHEGA
    try:
        with open(ARQUIVO_CACHE, "r", encoding="utf-8") as f:
            alarmes_atuais = json.load(f)

        alarmes_atuais.sort(
        key=lambda x: x.get("alarmeDhCad") or "", 
        reverse=True
        )

        #json.dumps joga tudo para a IA
        dados_para_ia = json.dumps(alarmes_atuais, indent=2, ensure_ascii=False)
        print(f"[BOT] Lendo JSON: {len(alarmes_atuais)}")
    except FileNotFoundError:
        dados_para_ia = "[]"
        print("[BOT] ❌ AVISO: cache_alarmes.json não encontrado!")
        
    # 3. MONTA O PROMPT DINÂMICO
    instrucao_do_sistema = f"""
    Você é o assistente virtual de suporte técnico da Eletrofrio Refrigeração.
    Estes são os alarmes ativos no momento, baseie suas resposta nestes dados:
    {dados_para_ia}
    
    Responda à pergunta do usuário de forma amigável e concisa para o WhatsApp, baseando-se SOMENTE nesses alarmes.
    REGRA CRITICA: para saber a data real de QUANDO UM ALARME FOI ABERTO, se baseie no campo "alarmeDhCad" exclusivamente, 
    NUNCA se baseie no campo "alarmeDesc", NUNCA
    """

    # 4. CHAMA A IA
    try:
        chat = client.chats.create(
            model='gemini-2.5-flash',
            config=types.GenerateContentConfig(
                system_instruction=instrucao_do_sistema, 
                temperature=0.2
            )
        )
        response = chat.send_message(mensagem_usuario)
        return response.text
    except Exception as e:
        print(f"Erro na IA: {e}")
        return "Desculpe, meu cérebro (IA) está passando por instabilidades. Tente novamente."
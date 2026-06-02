import json
import os
import threading
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client as TwilioClient
from dotenv import load_dotenv
from bot_integrado import consultar_ia

load_dotenv()

app = Flask(__name__)

ARQUIVO_CACHE    = "banco_local/cache_alarmes.json"
ARQUIVO_CONTATOS = "banco_local/mapa_contatos.json"
LABEL_CRITICIDADE = {"C": "🔴 Crítico", "A": "🟠 Alto", "M": "🟡 Médio"}

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS PARA O MENU
# ──────────────────────────────────────────────────────────────────────────────

def carregar_lojas_do_numero(numero: str) -> list:
    if not os.path.exists(ARQUIVO_CONTATOS):
        return []
    try:
        with open(ARQUIVO_CONTATOS, 'r', encoding='utf-8') as f:
            mapa = json.load(f)
        numero_limpo = numero.replace("whatsapp:", "").strip()
        return [
            loja_id for loja_id, tel in mapa.items()
            if not loja_id.startswith("__") and tel.replace(" ", "") == numero_limpo
        ]
    except Exception:
        return []


def listar_alarmes_para_numero(numero: str) -> str:
    try:
        with open(ARQUIVO_CACHE, 'r', encoding='utf-8') as f:
            todos_alarmes = json.load(f)
    except Exception:
        return "❌ Não foi possível carregar os alarmes no momento. Tente novamente."

    lojas_do_numero = carregar_lojas_do_numero(numero)
    alarmes = (
        [a for a in todos_alarmes if str(a.get('lojaId', '')) in lojas_do_numero]
        if lojas_do_numero else todos_alarmes
    )

    if not alarmes:
        return "✅ Nenhum alarme ativo no momento para as suas lojas."

    linhas = [f"📋 *Alarmes ativos — {len(alarmes)} total*\n"]
    for cod, label in LABEL_CRITICIDADE.items():
        grupo = [a for a in alarmes if a.get('criticidade') == cod]
        if not grupo:
            continue
        linhas.append(f"\n{label} ({len(grupo)})")
        for a in grupo[:5]:
            loja  = a.get('lojaNm', '?')
            desc  = a.get('alarmeDesc', '?')
            tempo = a.get('tempo', '?')
            linhas.append(f"• *{loja}* — {desc} _{tempo}_")
        if len(grupo) > 5:
            linhas.append(f"  _(+ {len(grupo) - 5} mais...)_")

    linhas.append("\n_Para mais detalhes, envie sua dúvida e a IA responde (opção 3)._")
    return "\n".join(linhas)

# ──────────────────────────────────────────────────────────────────────────────
# RESPOSTA ASSÍNCRONA — resolve o timeout do Twilio
# ──────────────────────────────────────────────────────────────────────────────

def dividir_mensagem(mensagem: str, limite: int = 1500) -> list:
    """
    Divide uma mensagem longa em partes de até `limite` caracteres.
    Tenta quebrar em linhas para não cortar no meio de uma frase.
    """
    if len(mensagem) <= limite:
        return [mensagem]

    partes = []
    while mensagem:
        if len(mensagem) <= limite:
            partes.append(mensagem.strip())
            break
        # Tenta cortar na última quebra de linha antes do limite
        corte = mensagem.rfind('\n', 0, limite)
        if corte == -1:  # Sem quebra de linha — corta no espaço mais próximo
            corte = mensagem.rfind(' ', 0, limite)
        if corte == -1:  # Sem espaço — força o corte no limite
            corte = limite
        partes.append(mensagem[:corte].strip())
        mensagem = mensagem[corte:].strip()

    return partes


def enviar_resposta_twilio(para: str, mensagem: str):
    """
    Envia uma mensagem proativamente via Twilio REST API.
    Divide automaticamente em partes se ultrapassar 1500 caracteres.
    """
    account_sid   = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token    = os.getenv("TWILIO_AUTH_TOKEN")
    numero_twilio = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

    if not account_sid or not auth_token:
        print(f"[ASYNC] ⚠️  Credenciais Twilio não configuradas. Resposta perdida para {para}.")
        return

    partes = dividir_mensagem(mensagem)
    total  = len(partes)

    try:
        client = TwilioClient(account_sid, auth_token)
        for i, parte in enumerate(partes):
            # Adiciona indicador de parte só se houver mais de uma
            corpo = f"_{i+1}/{total}_\n{parte}" if total > 1 else parte
            client.messages.create(from_=numero_twilio, body=corpo, to=para)
            print(f"[ASYNC] ✅ Parte {i+1}/{total} enviada para {para} ({len(corpo)} chars)")
    except Exception as e:
        print(f"[ASYNC] ❌ Erro ao enviar resposta: {e}")


def processar_e_responder(numero_cliente: str, mensagem_cliente: str):
    """
    Roda em background: chama a IA e envia a resposta via REST API.
    Isso evita o timeout de 15s do Twilio para consultas demoradas.
    """
    print(f"[ASYNC] Processando IA para {numero_cliente}...")

    ia_terminou = threading.Event()

    def vigia_de_tempo():
        # o .wait(60) ele pausa aquela linha que ele foi inserida por 60 segundos
        # se a IA terminar antes destes 60 segundos, o wait é cancelado
        nao_terminou = not ia_terminou.wait(60.0)

        # se passou 60 segundos sem resposta, ativa este if 
        if nao_terminou: 
            print(f"[Aviso] a IA está demorando para responder {numero_cliente}...")
            mensagem_demora = "⏳ *Aguarde mais um instante...*\nO raciocínio está demorando um pouco mais do que o esperado, mas já te respondo!"
            enviar_resposta_twilio(mensagem_demora)
        
    threading.Thread(target=vigia_de_tempo,daemon=True).start()

    #bloco seguro para consulta com a IA
    try:
        resposta_texto = consultar_ia(mensagem_cliente, numero_cliente)
        #sucesso! então é parado o cronometro
        ia_terminou.set()

    except Exception as e:
        #no caso de erro também para o cronometro
        ia_terminou.set()
        resposta_texto = f"❌ Erro interno ao consultar a IA: {e}"
        print(f"[ASYNC] Erro na IA: {e}")

    
    enviar_resposta_twilio(numero_cliente, resposta_texto)

# ──────────────────────────────────────────────────────────────────────────────
# ROTAS FLASK
# ──────────────────────────────────────────────────────────────────────────────

@app.route('/', methods=['GET'])
def index():
    return "Servidor Online!", 200


@app.route('/webhook', methods=['POST'])
def webhook_whatsapp():
    mensagem_cliente = request.values.get('Body', '').strip()
    numero_cliente   = request.values.get('From', '')

    print(f"\n📱 NOVA MENSAGEM RECEBIDA!")
    print(f"De: {numero_cliente} | Texto: {mensagem_cliente}")

    resposta = MessagingResponse()

    # ── Opções do menu — resposta rápida, sem IA ────────────────────────────
    if mensagem_cliente == '1':
        resposta.message(listar_alarmes_para_numero(numero_cliente))
        return str(resposta), 200, {'Content-Type': 'application/xml'}

    elif mensagem_cliente == '2':
        resposta.message(
            "📞 *Equipe de Suporte Técnico — Eletrofrio*\n\n"
            "Entre em contato pelos canais:\n"
            "• 📞 Telefone: (41) 3333-4444\n"
            "• 📧 E-mail: suporte@eletrofrio.com.br\n"
            "• ⏰ Atendimento: Seg a Sex, das 8h às 18h\n\n"
            "Um técnico entrará em contato em breve! ✅\n\n"
            "_Para continuar, basta enviar sua dúvida ou digitar 3 para a IA._"
        )
        return str(resposta), 200, {'Content-Type': 'application/xml'}

    elif mensagem_cliente.upper().startswith("IA"):
        # Dispara a IA em segundo plano (Thread) para ela trabalhar sem travar o servidor
        thread = threading.Thread(
            target=processar_e_responder,
            args=(numero_cliente, mensagem_cliente),
            daemon=True
        )
        thread.start()
        resposta.message("⏳ *A IA está analisando os dados.* Aguarde um momento...")
        return str(resposta), 200, {'Content-Type': 'application/xml'}
    
    else:
        resposta.message(
            "👋 *Olá! Sou o Assistente Virtual Eletrofrio.*\n\n"
            "Escolha uma opção digitando o número correspondente:\n"
            "1️⃣ Ver meus alarmes ativos\n"
            "2️⃣ Falar com o suporte humano\n\n"
            "🤖 *Quer perguntar algo específico para a IA?*\n"
            "Comece a sua mensagem com a palavra *IA*.\n"
            "_Exemplo: IA, qual equipamento está há mais tempo com defeito?_"
        )
        return str(resposta), 200, {'Content-Type': 'application/xml'}


if __name__ == '__main__':
    print("Iniciando servidor Flask...")
    app.run(port=5000, debug=True)

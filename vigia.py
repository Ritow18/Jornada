import time
import json
import os
from datetime import datetime, timedelta
from collections import Counter
from dotenv import load_dotenv
from eletrofrio_api import buscar_alarmes

load_dotenv()

PASTA_BANCO      = "banco_local"
ARQUIVO_CACHE    = f"{PASTA_BANCO}/cache_alarmes.json"
ARQUIVO_CONTATOS = f"{PASTA_BANCO}/mapa_contatos.json"

# Mapa de criticidade para exibição
LABEL_CRITICIDADE = {"C": "🔴 Crítico", "A": "🟠 Alto", "M": "🟡 Médio"}

os.makedirs(PASTA_BANCO, exist_ok=True)

# ──────────────────────────────────────────────────────────────────────────────
# CACHE
# ──────────────────────────────────────────────────────────────────────────────

def carregar_cache() -> list:
    if not os.path.exists(ARQUIVO_CACHE):
        print("arquivo não encontrado, criando arquivo com dados de segurança")
        dados_seguranca = [
            {
                "contaId": 2,
                "contaNm": "Jacomar",
                "lojaId": 335,
                "lojaNm": "Pedro Gusso",
                "nrPedido": "077.018.23",
                "dispositivoId": 34262,
                "dispositivoNm": "BUFFET ROTISSERIA",
                "grupoNm": "Outros",
                "subgrupoNm": "Trocador de Calor",
                "alarmeId": 4207529,
                "alarmeDhCad": "2026-05-19T00:07:17",
                "alarmeDesc": "Alarme - OFFLINE [Alto]",
                "silenciarAte": None,
                "criticidade": "C",
                "ppAbertura": "C",
                "eventoDhCad": None,
                "eventoDesc": None,
                "eventoUsu": None,
                "tempo": "3m"
            },
            {
                "contaId": 3,
                "contaNm": "Fort",
                "lojaId": 438,
                "lojaNm": "Piraquara",
                "nrPedido": "077.126.22",
                "dispositivoId": 25227,
                "dispositivoNm": "Ilha - ICF 3",
                "grupoNm": "Ambiente",
                "subgrupoNm": "Ilha Self",
                "alarmeId": 4207540,
                "alarmeDhCad": "2026-05-19T00:09:48",
                "alarmeDesc": "Alarme de alta temperatura [Alto]",
                "silenciarAte": None,
                "criticidade": "A",
                "ppAbertura": "C",
                "eventoDhCad": None,
                "eventoDesc": None,
                "eventoUsu": None,
                "tempo": "54m"
            }
        ]
        # Garante que a pasta 'banco_local' existe
        os.makedirs(os.path.dirname(ARQUIVO_CACHE), exist_ok=True)
        
        # Cria o arquivo físico e salva os dados de segurança nele
        with open(ARQUIVO_CACHE, 'w', encoding='utf-8') as f:
            json.dump(dados_seguranca, f, indent=2, ensure_ascii=False)
            
        return dados_seguranca
    
    #se o arquivo existir, vem pra ca
    try:
        with open(ARQUIVO_CACHE, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        if not isinstance(dados, list):
            print(f"⚠️ Cache corrompido (tipo: {type(dados).__name__}). Ignorando e resetando.")
            return []
        return dados
    except Exception as e:
        print(f" Erro ao ler cache: {e}. Resetando.")
        return []


def salvar_cache(dados: list):
    if not dados:
        print(" API retornou lista vazia — cache NÃO será sobrescrito para preservar o estado anterior.")
        return
    try:
        with open(ARQUIVO_CACHE, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Erro crítico ao salvar cache: {e}")

# ──────────────────────────────────────────────────────────────────────────────
# MAPA DE CONTATOS (lojaId → número WhatsApp do responsável)
# ──────────────────────────────────────────────────────────────────────────────

def carregar_mapa_contatos() -> dict:
    """
    Carrega o mapeamento lojaId → número WhatsApp do arquivo mapa_contatos.json.
    Se o arquivo não existir, cria um template para o usuário preencher.
    Formato do número: +55DDDNUMERO (ex: +5541999999999)
    """
    if not os.path.exists(ARQUIVO_CONTATOS):
        template = {
            "__instrucoes__": (
                "Mapeie o lojaId (número inteiro da loja na API) ao número WhatsApp "
                "do responsável. Formato do número: +55DDDNUMERO. "
                "Veja os lojaIds no cache_alarmes.json."
            ),
            "760": "+5541999999999",
            "777": "+5541988888888"
        }
        with open(ARQUIVO_CONTATOS, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        print(
            f"\n[VIGIA] ⚠️  Arquivo '{ARQUIVO_CONTATOS}' criado com valores de exemplo.\n"
            f"         Edite-o com os números reais antes de usar em produção!\n"
        )
        return {}

    try:
        with open(ARQUIVO_CONTATOS, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        # Remove chaves especiais de metadados
        return {k: v for k, v in dados.items() if not k.startswith("__")}
    except Exception as e:
        print(f"[VIGIA] Erro ao carregar mapa de contatos: {e}")
        return {}

# ──────────────────────────────────────────────────────────────────────────────
# MONTAGEM DE MENSAGENS WHATSAPP
# ──────────────────────────────────────────────────────────────────────────────

def montar_mensagem_whatsapp(alarmes_novos: list) -> str:
    """Resumo geral de novos alarmes (usado internamente para log/debug)."""
    qtd = len(alarmes_novos)
    criticos = [a for a in alarmes_novos if a.get('criticidade') == 'C']

    if criticos:
        linhas = [f"🔴 *ALERTA CRÍTICO — Eletrofrio* 🔴\n"]
        linhas.append(f"{len(criticos)} alarme(s) *CRÍTICO(s)* detectado(s):\n")
        for a in criticos[:5]:
            linhas.append(f"• {a.get('lojaNm','?')} — {a.get('alarmeDesc','?')}")
        if len(criticos) > 5:
            linhas.append(f"... e mais {len(criticos)-5} crítico(s).")
        linhas.append(f"\nTotal de novos alarmes: {qtd}")
    else:
        linhas = [f"⚠️ *Eletrofrio Alertas* ⚠️\n"]
        linhas.append(f"Você tem *{qtd}* novo(s) alarme(s) nas suas lojas.")

    return "\n".join(linhas)


def montar_mensagem_alerta_critico(loja_nm: str, alarmes_criticos: list) -> str:
    """
    Monta a mensagem pré-escrita de alerta crítico com menu de ações,
    enviada proativamente ao responsável pela loja.
    """
    qtd = len(alarmes_criticos)

    linhas = [
        "🔴 *ALERTA CRÍTICO — Eletrofrio* 🔴",
        "",
        f"*{qtd} alarme(s) crítico(s)* detectado(s) em *{loja_nm}*:",
        "",
    ]

    for a in alarmes_criticos[:3]:
        disp = a.get('dispositivoNm', '?')
        desc = a.get('alarmeDesc', '?')
        linhas.append(f"• *{disp}:* {desc}")

    if qtd > 3:
        linhas.append(f"_(... e mais {qtd - 3} alarme(s) crítico(s))_")

    linhas.extend([
        "",
        "Como você gostaria de tomar uma ação?",
        "",
        "*1* — 📋 Visualizar todos os alarmes",
        "*2* — 📞 Contatar a equipe de suporte técnico",
        "*3* — 🤖 Perguntar à IA",
    ])

    return "\n".join(linhas)

# ──────────────────────────────────────────────────────────────────────────────
# ENVIO WHATSAPP VIA TWILIO
# ──────────────────────────────────────────────────────────────────────────────

def enviar_alerta_whatsapp(numero: str, mensagem: str) -> bool:
    """
    Envia uma mensagem WhatsApp via Twilio REST API.
    Se as credenciais não estiverem configuradas no .env, faz simulação no terminal.
    Retorna True se enviado com sucesso, False caso contrário.

    Variáveis necessárias no .env:
        TWILIO_ACCOUNT_SID   → Account SID do painel Twilio
        TWILIO_AUTH_TOKEN    → Auth Token do painel Twilio
        TWILIO_WHATSAPP_FROM → Número Twilio (ex: whatsapp:+14155238886)
    """
    from twilio.rest import Client as TwilioClient

    account_sid    = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token     = os.getenv("TWILIO_AUTH_TOKEN")
    numero_twilio  = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

    if not account_sid or not auth_token:
        # Modo simulação — útil durante desenvolvimento
        print("⚠️  Configure TWILIO_ACCOUNT_SID e TWILIO_AUTH_TOKEN no .env para envios reais.")
        return False

    try:
        client = TwilioClient(account_sid, auth_token)
        msg = client.messages.create(
            from_=numero_twilio,
            body=mensagem,
            to=numero if numero.startswith("whatsapp:") else f"whatsapp:{numero}"
        )
        print(f"[WHATSAPP] ✅ Alerta enviado para {numero} (SID: {msg.sid})")
        return True
    except Exception as e:
        print(f"[WHATSAPP] ❌ Erro ao enviar para {numero}: {e}")
        return False


def enviar_alertas_criticos_por_loja(alarmes_novos: list):
    """
    Agrupa os novos alarmes críticos por loja e envia um alerta WhatsApp
    ao número configurado para cada loja em mapa_contatos.json.
    Lojas sem número configurado recebem aviso no terminal.
    """
    mapa_contatos = carregar_mapa_contatos()

    # Agrupa alarmes críticos por lojaId
    criticos_por_loja: dict = {}
    for alarme in alarmes_novos:
        if alarme.get('criticidade') != 'C':
            continue
        loja_id = str(alarme.get('lojaId', ''))
        loja_nm = alarme.get('lojaNm', 'Desconhecida')
        if loja_id not in criticos_por_loja:
            criticos_por_loja[loja_id] = {'loja_nm': loja_nm, 'alarmes': []}
        criticos_por_loja[loja_id]['alarmes'].append(alarme)

    if not criticos_por_loja:
        return  # Nenhum crítico novo — nada a enviar

    print(f"\n{len(criticos_por_loja)} loja(s) com novos alarmes críticos. Enviando alertas...")

    for loja_id, info in criticos_por_loja.items():
        loja_nm = info['loja_nm']
        alarmes = info['alarmes']
        numero  = mapa_contatos.get(loja_id)

        if not numero:
            print(f"⚠️  Sem número configurado para '{loja_nm}' (lojaId: {loja_id}). Pulando.")
            continue

        mensagem = montar_mensagem_alerta_critico(loja_nm, alarmes)
        enviar_alerta_whatsapp(numero, mensagem)

# ──────────────────────────────────────────────────────────────────────────────
# VERIFICAÇÃO PRINCIPAL
# ──────────────────────────────────────────────────────────────────────────────

def verificar_mudancas():
    horario_atual = datetime.now().strftime('%H:%M:%S')
    dados_api = buscar_alarmes()

    if dados_api is None:
        print(" Falha ao conectar com a API. Cache preservado.")
        return

    if not isinstance(dados_api, list):
        print(f" Resposta da API com tipo inesperado ({type(dados_api).__name__}). Cache preservado.")
        return

    # ── Carrega estado anterior ──────────────────────────────────────────────
    alarmes_antigos = carregar_cache()
    ids_antigos = {a.get('alarmeId') for a in alarmes_antigos if a.get('alarmeId') is not None}

    # ── Detecta novos e resolvidos ───────────────────────────────────────────
    alarmes_novos      = [a for a in dados_api     if a.get('alarmeId') not in ids_antigos]
    ids_atuais         = {a.get('alarmeId') for a in dados_api if a.get('alarmeId') is not None}
    alarmes_resolvidos = [a for a in alarmes_antigos if a.get('alarmeId') not in ids_atuais]

    # ── Exibe resultado ──────────────────────────────────────────────────────
    if alarmes_novos:
        qtd = len(alarmes_novos)
        print(f"\n {qtd} NOVO(S) ALARME(S) DETECTADO(S)!")

        # # Resumo por loja
        # contagem_por_loja = Counter(a.get('lojaNm', 'Desconhecida') for a in alarmes_novos)
        # for loja, n in contagem_por_loja.items():
        #     print(f"   • {loja}: {n} novo(s)")

        # # Resumo por criticidade
        # for cod, label in LABEL_CRITICIDADE.items():
        #     grupo = [a for a in alarmes_novos if a.get('criticidade') == cod]
        #     if grupo:
        #         print(f"   {label}: {len(grupo)}")

        # ── Envia alertas WhatsApp para lojas com alarmes críticos ───────────
        enviar_alertas_criticos_por_loja(alarmes_novos)

        # Log dos não-críticos (sem envio automático)
        nao_criticos = [a for a in alarmes_novos if a.get('criticidade') != 'C']
        if nao_criticos:
            mensagem_resumo = montar_mensagem_whatsapp(nao_criticos)
            print(f"\n[LOG WHATSAPP — NÃO CRÍTICOS]\n{mensagem_resumo}\n")
    else:
        print("✅ Nenhum novo alarme desde a última checagem.")

    if alarmes_resolvidos:
        print(f"   ✔️ {len(alarmes_resolvidos)} alarme(s) resolvido(s)/saíram da API desde o último ciclo.")

    print(f"   📊 Ativos na API agora: {len(dados_api)}  |  Conhecidos no cache: {len(alarmes_antigos)}")

    salvar_cache(dados_api)

# ──────────────────────────────────────────────────────────────────────────────
# LOOP PRINCIPAL
# ──────────────────────────────────────────────────────────────────────────────

def esperar_proximo_ciclo():
    agora = datetime.now()
    minutos_sobrando = 5 - (agora.minute % 5)
    proximo_alvo = agora + timedelta(minutes=minutos_sobrando)
    proximo_alvo = proximo_alvo.replace(second=15)

    segundos_espera = (proximo_alvo - agora).total_seconds()

    if segundos_espera <= 0:
        segundos_espera = 300

    print(f"Proximo check-up: {proximo_alvo.strftime('%H:%M:%S')} ({int(segundos_espera)}s)...\n")
    time.sleep(segundos_espera)


if __name__ == "__main__":
    print("Vigia Iniciado!")
    while True:
        verificar_mudancas()
        esperar_proximo_ciclo()

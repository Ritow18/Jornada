import time
import json
import os
from datetime import datetime, timedelta
from collections import Counter
from eletrofrio_api import buscar_alarmes

PASTA_BANCO = "banco_local"
ARQUIVO_CACHE = f"{PASTA_BANCO}/cache_alarmes.json"

# Mapa de criticidade para exibição
LABEL_CRITICIDADE = {"C": "🔴 Crítico", "A": "🟠 Alto", "M": "🟡 Médio"}

os.makedirs(PASTA_BANCO, exist_ok=True)

def carregar_cache() -> list:
    """
    Lê o cache de alarmes do ciclo anterior.
    Retorna lista vazia se o arquivo não existir, estiver corrompido
    ou contiver um tipo inesperado (dict, null...).

    BUG ORIGINAL: o código anterior não validava o tipo do dado lido.
    Se uma resposta inesperada da API fosse salva (ex: um dict),
    o set-comprehension 'ids_antigos' iterava sobre as CHAVES do dict
    em vez dos alarmes, produzindo um set de strings como {"alarmes","total"}.
    Como alarme['alarmeId'] é um inteiro, ele nunca estava nesse set,
    então TODOS os alarmes eram detectados como "novos" a cada ciclo.
    """
    if not os.path.exists(ARQUIVO_CACHE):
        return []
    try:
        with open(ARQUIVO_CACHE, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        if not isinstance(dados, list):
            print(f"⚠️  Cache corrompido (tipo: {type(dados).__name__}). Ignorando e resetando.")
            return []
        return dados
    except Exception as e:
        print(f" Erro ao ler cache: {e}. Resetando.")
        return []


def salvar_cache(dados: list):
    """
    Salva o snapshot atual da API no cache.

    BUG ORIGINAL: o código anterior não tratava erro de escrita.
    Se a escrita falhasse silenciosamente, o cache ficava com dados
    do ciclo anterior e alarmes já vistos continuavam aparecendo como novos.
    Também não protegia contra sobrescrever com lista vazia em caso de
    falha momentânea da API.
    """
    if not dados:
        print(" API retornou lista vazia — cache NÃO será sobrescrito para preservar o estado anterior.")
        return
    try:
        with open(ARQUIVO_CACHE, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Erro crítico ao salvar cache: {e}")


# ─────────────────────────────────────────────
# WHATSAPP (simulação)
# ─────────────────────────────────────────────

def montar_mensagem_whatsapp(alarmes_novos: list) -> str:
    qtd = len(alarmes_novos)
    criticos = [a for a in alarmes_novos if a.get('criticidade') == 'C']

    if criticos:
        linhas = [f"🔴 *ALERTA CRÍTICO — Eletrofrio* 🔴\n"]
        linhas.append(f"{len(criticos)} alarme(s) *CRÍTICO(s)* detectado(s):\n")
        for a in criticos[:5]:  # máx 5 para não entupir o WhatsApp
            linhas.append(f"• {a.get('lojaNm','?')} — {a.get('alarmeDesc','?')}")
        if len(criticos) > 5:
            linhas.append(f"... e mais {len(criticos)-5} crítico(s).")
        linhas.append(f"\nTotal de novos alarmes: {qtd}")
        linhas.append("Gostaria de ver todos?")
    else:
        linhas = [f"⚠️ *Eletrofrio Alertas* ⚠️\n"]
        linhas.append(f"Você tem *{qtd}* novo(s) alarme(s) nas suas lojas.")
        linhas.append("Gostaria de vê-los?")

    return "\n".join(linhas)

def verificar_mudancas():
    horario_atual = datetime.now().strftime('%H:%M:%S')
    print(f"[{horario_atual}] Buscando atualizações na Eletrofrio...")

    dados_api = buscar_alarmes()

    if dados_api is None:
        print("❌ Falha ao conectar com a API. Cache preservado.")
        return

    # Proteção extra: garante que a API devolveu uma lista
    if not isinstance(dados_api, list):
        print(f"❌ Resposta da API com tipo inesperado ({type(dados_api).__name__}). Cache preservado.")
        return

    # ── Carrega estado anterior ──────────────────────────────────────────────
    alarmes_antigos = carregar_cache()

    # Conjunto de IDs já conhecidos — usa .get() para não quebrar se algum
    # alarme estiver malformado e não tiver a chave 'alarmeId'
    ids_antigos = {a.get('alarmeId') for a in alarmes_antigos if a.get('alarmeId') is not None}

    # ── Detecta novos e resolvidos ───────────────────────────────────────────
    alarmes_novos     = [a for a in dados_api   if a.get('alarmeId') not in ids_antigos]
    ids_atuais        = {a.get('alarmeId') for a in dados_api if a.get('alarmeId') is not None}
    alarmes_resolvidos = [a for a in alarmes_antigos if a.get('alarmeId') not in ids_atuais]

    # ── Exibe resultado ──────────────────────────────────────────────────────
    if alarmes_novos:
        qtd = len(alarmes_novos)
        print(f"\n {qtd} NOVO(S) ALARME(S) DETECTADO(S)!")

        # Resumo por loja
        contagem_por_loja = Counter(a.get('lojaNm', 'Desconhecida') for a in alarmes_novos)
        for loja, n in contagem_por_loja.items():
            print(f"   • {loja}: {n} novo(s)")

        # Resumo por criticidade
        for cod, label in LABEL_CRITICIDADE.items():
            grupo = [a for a in alarmes_novos if a.get('criticidade') == cod]
            if grupo:
                print(f"   {label}: {len(grupo)}")

        # Mensagem WhatsApp — envia só se tiver crítico OU sempre (ajuste aqui)
        criticos = [a for a in alarmes_novos if a.get('criticidade') == 'C']
        if criticos:
            mensagem = montar_mensagem_whatsapp(alarmes_novos)
            print(f"\n[SIMULAÇÃO WHATSAPP — CRÍTICO]\n{mensagem}\n")
        else:
            # Para alarmes não-críticos, você pode optar por não enviar ou enviar resumo
            mensagem = montar_mensagem_whatsapp(alarmes_novos)
            print(f"\n[SIMULAÇÃO WHATSAPP — RESUMO]\n{mensagem}\n")
    else:
        print("✅ Nenhum novo alarme desde a última checagem.")

    if alarmes_resolvidos:
        print(f"   ✔️  {len(alarmes_resolvidos)} alarme(s) resolvido(s)/saíram da API desde o último ciclo.")

    print(f"   📊 Ativos na API agora: {len(dados_api)}  |  Conhecidos no cache: {len(alarmes_antigos)}")

    salvar_cache(dados_api)

def esperar_proximo_ciclo():
    agora = datetime.now()
    minutos_sobrando = 5 - (agora.minute % 5)
    proximo_alvo = agora + timedelta(minutes=minutos_sobrando)
    proximo_alvo = proximo_alvo.replace(second=15)

    segundos_espera = (proximo_alvo - agora).total_seconds()

    # Proteção: se o cálculo der <= 0 (ex: rodou exatamente no :30), espera 5 min
    if segundos_espera <= 0:
        segundos_espera = 300

    print(f"Proximo check-up: {proximo_alvo.strftime('%H:%M:%S')} ({int(segundos_espera)}s)...\n")
    time.sleep(segundos_espera)


if __name__ == "__main__":
    print("Vigia da Eletrofrio — Detector de Novidades Iniciado!")
    print("=" * 55)
    while True:
        verificar_mudancas()
        esperar_proximo_ciclo()
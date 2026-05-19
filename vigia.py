import time
import json
import os
from datetime import datetime, timedelta
from collections import Counter  # Biblioteca nativa para contar coisas fácil
from eletrofrio_api import buscar_alarmes

PASTA_BANCO = "banco_local"
ARQUIVO_CACHE = f"{PASTA_BANCO}/cache_alarmes.json"

os.makedirs(PASTA_BANCO, exist_ok=True)

def verificar_mudancas():
    horario_atual = datetime.now().strftime('%H:%M:%S')
    print(f"[{horario_atual}] Buscando atualizações na Eletrofrio...")
    
    dados_api = buscar_alarmes()
    
    if dados_api is None:
        print("❌ Falha ao conectar com a API.")
        return

    alarmes_antigos = []
    # 1. Se o arquivo já existir, lê os alarmes anteriores
    if os.path.exists(ARQUIVO_CACHE):
        try:
            with open(ARQUIVO_CACHE, 'r', encoding='utf-8') as f:
                alarmes_antigos = json.load(f)
        except Exception as e:
            print(f"Erro ao ler cache antigo: {e}")

    # 2. Cria um conjunto (set) apenas com os IDs dos alarmes antigos para busca rápida
    ids_antigos = {alarme['alarmeId'] for alarme in alarmes_antigos}

    # 3. Descobre quais alarmes são novos filtrando os que não estavam no cache
    alarmes_novos_detectados = []
    for alarme in dados_api:
        if alarme['alarmeId'] not in ids_antigos:
            alarmes_novos_detectados.append(alarme)

    # 4. Se encontrou novidades, faz a contagem e monta a mensagem
    if alarmes_novos_detectados:
        qtd_total = len(alarmes_novos_detectados)
        print(f"\n {qtd_total} NOVO(S) ALARME(S) DETECTADO(S)!")
        
        # Conta quantos alarmes novos cada mercado (lojaNm) teve
        # Ex: Counter(['Fort', 'Fort', 'Jacomar']) -> {'Fort': 2, 'Jacomar': 1}
        lojas_afetadas = [alarme['lojaNm'] for alarme in alarmes_novos_detectados]
        contagem_por_loja = Counter(lojas_afetadas)
        
        # Mostra o resumo no terminal
        for loja, qtd in contagem_por_loja.items():
            print(f"   • {loja}: {qtd} novo(s) alarme(s)")
            
        # 5. PREPARA A MENSAGEM DO WHATSAPP
        # (Aqui criamos a string exata que vamos enviar pro cliente no futuro)
        mensagem_whatsapp = f"⚠️ *Eletrofrio Alertas* ⚠️\n\nVocê tem {qtd_total} novos alarmes nas suas lojas. Gostaria de vê-los?"
        print(f"\n[SIMULAÇÃO WHATSAPP] Enviando texto:\n{mensagem_whatsapp}\n")
    else:
        print("✅ Nenhuma alteração ou novo alarme desde a última checagem,seu bosta.")

    # 6. Atualiza o cache local salvando a foto atual da API por cima da antiga
    with open(ARQUIVO_CACHE, 'w', encoding='utf-8') as f:
        json.dump(dados_api, f, indent=2, ensure_ascii=False)


def esperar_proximo_ciclo():
    agora = datetime.now()
    minutos_sobrando = 5 - (agora.minute % 5)
    proximo_alvo = agora + timedelta(minutes=minutos_sobrando)
    proximo_alvo = proximo_alvo.replace(second=30, microsecond=0)
    
    segundos_espera = (proximo_alvo - agora).total_seconds()
    print(f"⏰ Dormindo até {proximo_alvo.strftime('%H:%M:%S')}...\n")
    time.sleep(segundos_espera)

if __name__ == "__main__":
    print("👀 Vigia da Eletrofrio com Detector de Novidades Iniciado!")
    while True:
        verificar_mudancas()
        esperar_proximo_ciclo()
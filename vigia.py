import time
import json
import requests
import os
import traceback
from datetime import datetime, timedelta

URL_ALARMES = "https://credenciamento.eletrofrio.com.br:5900/galileo/api/api_hackathon?route=alarmes"
ARQUIVO_CACHE = "cache_alarmes.json"

def verificar_mudancas():
    print("Buscando dados na Eletrofrio...")
    
    try:
        resposta = requests.get(URL_ALARMES,timeout=30)
        if resposta.status_code == 200:
            dados_novos = resposta.json()
            
            # 1. Verifica se já temos um cache salvo anteriormente
            if os.path.exists(ARQUIVO_CACHE):
                with open(ARQUIVO_CACHE, 'r', encoding='utf-8') as f:
                    dados_antigos = json.load(f)
                
                # Conta quantos alarmes tínhamos antes e quantos temos agora
                if len(dados_novos) > len(dados_antigos):
                    print("Novo alarme detectado!")
                    # (aqui vai a linha de código que manda outro arquivo especializado somente para mensagem pro WhatsApp)
                else:
                    print("sem alarmes novos.")
            
            # 2. Salva os dados novos no arquivo de cache local
            with open(ARQUIVO_CACHE, 'w', encoding='utf-8') as f:
                json.dump(dados_novos, f, indent=4, ensure_ascii=False)
                
    except Exception as e:
        print(f"Erro ao conectar: {e}")
        traceback.print_exc()

def esperar_proximo_ciclo():
    agora = datetime.now()
    minutos_sobrando = 5 - (agora.minute % 5)
    # Calcula quantos minutos faltam para o próximo múltiplo de 5

    proximo_alvo = agora + timedelta(minutes=minutos_sobrando)

    # Zera os milissegundos e crava os segundos em 15 (nossa margem de segurança!)
    # Exemplo: se agora são 21:02, o alvo vira 21:05:15
    proximo_alvo = proximo_alvo.replace(second=15,microsecond=0)
    segunda_espera = (proximo_alvo - agora).total_seconds()

    print(f"proxima checagem sincronizada ficou para {proximo_alvo.strftime('%H:%M:%S')}")
    time.sleep(segunda_espera)

# Loop infinito do Vigia
print("Iniciando o Vigia da Eletrofrio...")
while True:
    verificar_mudancas()
    esperar_proximo_ciclo()
    print("Indo dormir por 5 minutos...\n")
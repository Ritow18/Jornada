import subprocess
import sys
import time

print("Iniciando a Infraestrutura")

processos = []

try:
    print("1. Subindo o servidor Flask...")
    proc_flask = subprocess.Popen([sys.executable, "servidor_flask.py"])
    processos.append(proc_flask)
    
    # Dá um tempinho para o servidor respirar
    time.sleep(3)

    print("2. Subindo o Ngrok...")
    proc_ngrok = subprocess.Popen(["ngrok", "http", "5000"])
    processos.append(proc_ngrok)
    
    # Dá um tempinho para o túnel do Ngrok ser criado
    time.sleep(3)

    print("3. Subindo o Vigia...")
    proc_vigia = subprocess.Popen([sys.executable, "vigia.py"])
    processos.append(proc_vigia)
    
    # mais um tempinho pra evitar problema
    time.sleep(3)

    print("3. Subindo o bot_integrado...")
    proc_bot = subprocess.Popen([sys.executable, "bot_integrado.py"])
    processos.append(proc_bot)

    print("INFRAESTRUTURA RODANDO (Flask, Ngrok, Vigia e o Bot)")

    while True:
        time.sleep(1)

except KeyboardInterrupt:
    # O bloco "salva-vidas": se você der Ctrl+C no terminal, ele mata tudo
    print("\n\n🛑 Encerrando todos os sistemas (Flask, Ngrok e Vigia e o bot)...")
    for p in processos:
        p.terminate()
    print("Sistemas encerrados com sucesso.")
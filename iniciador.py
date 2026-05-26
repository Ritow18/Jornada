import subprocess
import sys
import time

print("Iniciando o Ecossistema Eletrofrio...")
print("-" * 50)

processos = []

try:
    print("Subindo o servidor Flask...")
    proc_flask = subprocess.Popen([sys.executable, "servidor_flask.py"])
    processos.append(proc_flask)
    
    # Dá um tempinho para o servidor respirar antes de subir o próximo
    time.sleep(4)

    print("Subindo o Chatbot Integrado...")
    proc_bot = subprocess.Popen([sys.executable, "bot_integrado.py"])
    processos.append(proc_bot)

    # 3. Mantém o iniciador rodando até você decidir parar
    print("\n✅ Sistema Operacional Eletrofrio Online. Pressione Ctrl+C para derrubar tudo.\n")
    proc_bot.wait() # O script fica travado aqui esperando o bot terminar

except KeyboardInterrupt:
    # O bloco "salva-vidas": se você cancelar no terminal, ele mata os processos órfãos
    print("\n\n🛑 Encerrando todos os sistemas...")
    for p in processos:
        p.terminate()
    print("Desligamento concluído.")
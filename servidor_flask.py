from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return "Servidor Eletrofrio está Online!", 200

# O Webhook: a rota que o WhatsApp vai chamar quando chegar mensagem
@app.route('/webhook', methods=['POST'])
def webhook_whatsapp():
    # Pega os dados que o WhatsApp enviou (o JSON da mensagem)
    dados = request.get_json()
    
    print("\n--- NOVA MENSAGEM RECEBIDA ---")
    print(dados) 
    
    # Aqui, no futuro, vamos pegar o texto do cliente e mandar para o bot_integrado.py (A IA)
    # E depois mandar a resposta da IA de volta pro WhatsApp
    
    return jsonify({"status": "recebido"}), 200

if __name__ == '__main__':
    # Roda o servidor na porta 5000 do seu computador
    print("Iniciando servidor Flask...")
    app.run(port=5000, debug=True)
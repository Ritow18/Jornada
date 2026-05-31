from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse 
from bot_integrado  import consultar_ia

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return "Servidor Online!", 200

# O Webhook: a rota que o WhatsApp vai chamar quando chegar mensagem
@app.route('/webhook', methods=['POST'])
def webhook_whatsapp():
    # A Twilio envia o texto da mensagem no campo 'Body' e o remetente no 'From'
    mensagem_cliente = request.values.get('Body', '').strip()
    numero_cliente = request.values.get('From', '')
    
    print(f"\n📱 NOVA MENSAGEM RECEBIDA!")
    print(f"De: {numero_cliente} | Texto: {mensagem_cliente}")
    
    # 1. Pede para a IA processar a mensagem passando o número (para contexto futuro)
    resposta_da_ia = consultar_ia(mensagem_cliente, numero_cliente)
    
    # 2. Envia a resposta da IA de volta para o Twilio
    resposta = MessagingResponse()
    resposta.message(resposta_da_ia)
    
    # Retorna a resposta no formato XML que a Twilio exige
    return str(resposta), 200, {'Content-Type': 'application/xml'}

if __name__ == '__main__':
    print("Iniciando servidor Flask...")
    app.run(port=5000, debug=True)
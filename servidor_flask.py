from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse 

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return "Servidor Eletrofrio está Online!", 200

# O Webhook: a rota que o WhatsApp vai chamar quando chegar mensagem
@app.route('/webhook', methods=['POST'])
def webhook_whatsapp():
    # A Twilio envia o texto da mensagem no campo 'Body' e o remetente no 'From'
    mensagem_cliente = request.values.get('Body', '').strip()
    numero_cliente = request.values.get('From', '')
    
    print(f"\n📱 NOVA MENSAGEM RECEBIDA!")
    print(f"De: {numero_cliente}")
    print(f"Texto: {mensagem_cliente}")
    print("-" * 40)
    
    # Prepara a resposta que será enviada de volta para o WhatsApp
    resposta = MessagingResponse()
    
    # Aqui é uma simulação. Em breve, a IA é que vai gerar este texto!
    resposta.message(f"Olá! Você disse: '{mensagem_cliente}'. O meu cérebro de IA ainda está a ser conectado, mas já te consigo ouvir!")
    
    # Retorna a resposta no formato XML que a Twilio exige
    return str(resposta), 200, {'Content-Type': 'application/xml'}

if __name__ == '__main__':
    # Roda o servidor na porta 5000 do seu computador
    print("Iniciando servidor Flask...")
    app.run(port=5000, debug=True)
import requests

# A URL base que a faculdade passou
BASE_URL = "https://credenciamento.eletrofrio.com.br:5900/galileo/api/api_hackathon"

def buscar_alarmes():
    url = f"{BASE_URL}?route=alarmes"
    try:
        resposta = requests.get(url)
        # Se o servidor responder 200 (OK), transformamos o texto em um dicionário Python (JSON)
        if resposta.status_code == 200:
            return resposta.json()
        
    except Exception as e:
        print(f"Erro ao conectar com a Eletrofrio: {e}")
        return None

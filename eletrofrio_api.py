import requests

# A URL base que a faculdade passou
BASE_URL = "https://credenciamento.eletrofrio.com.br:5900/galileo/api/api_hackathon"

def buscar_alarmes():
    print("Buscando alarmes no servidor da Eletrofrio...")
    
    # Monta a URL completa para a rota de alarmes
    url = f"{BASE_URL}?route=alarmes"
    
    try:
        # Faz a requisição GET (como se você abrisse no navegador)
        resposta = requests.get(url)
        
        # Se o servidor responder 200 (OK), transformamos o texto em um dicionário Python (JSON)
        if resposta.status_code == 200:
            dados_alarmes = resposta.json()
            
            # Vamos imprimir quantos alarmes tem e mostrar só o primeiro para não sujar o terminal
            print(f"Sucesso! Encontramos {len(dados_alarmes)} alarmes registrados.")
            print("\nDetalhes do primeiro alarme:")
            
            # Pegando dados específicos do primeiro item da lista [0]
            primeiro_alarme = dados_alarmes[0]
            print(f"Loja: {primeiro_alarme['lojaNm']}")
            print(f"Dispositivo: {primeiro_alarme['dispositivoNm']}")
            print(f"Problema: {primeiro_alarme['alarmeDesc']}")
            print(f"Criticidade: {primeiro_alarme['criticidade']}")
            
            return dados_alarmes
        else:
            print(f"Erro na API. Código de status: {resposta.status_code}")
            return None
            
    except Exception as e:
        print(f"Erro ao conectar com a Eletrofrio: {e}")
        return None

# Testa a função se rodarmos este arquivo diretamente
if __name__ == "__main__":
    buscar_alarmes()
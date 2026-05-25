import requests

BASE_URL = "https://credenciamento.eletrofrio.com.br:5900/galileo/api/api_hackathon"

def buscar_alarmes():
    url = f"{BASE_URL}?route=alarmes"
    try:
        resposta = requests.get(url, timeout=30)

        if resposta.status_code == 200:
            dados = resposta.json()

            # Garante que a API retornou uma lista de alarmes (e não um dict de erro)
            if isinstance(dados, list):
                return dados
            else:
                print(f" API retornou um formato inesperado: {type(dados).__name__}. \
                      Dados esperado: list.")
                return None

        else:
            # BUG ORIGINAL: sem este return, a função retornava None implicitamente
            # porém sem nenhuma mensagem de erro, dificultando o diagnóstico
            print(f" API retornou status {resposta.status_code}: {resposta.text[:200]}")
            return None

    except requests.exceptions.Timeout:
        print(" Timeout ao conectar com a API (>30s).")
        return None
    except Exception as e:
        print(f" Erro ao conectar com a Eletrofrio: {e}")
        return None

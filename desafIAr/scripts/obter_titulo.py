import requests

def obter_titulo_youtube(video_url):
    """
    Busca o título do vídeo do YouTube utilizando o endpoint público de oEmbed.
    Não requer chaves de API restritas e funciona para vídeos públicos.
    """
    oembed_url = f"https://www.youtube.com/oembed?url={video_url}&format=json"
    
    try:
        response = requests.get(oembed_url, timeout=5)
        if response.status_code == 200:
            dados = response.json()
            return dados.get("title", "Vídeo sem título")
    except Exception as e:
        print(f"Erro ao buscar o título do YouTube: {e}")
        
    return "Vídeo em Processamento"

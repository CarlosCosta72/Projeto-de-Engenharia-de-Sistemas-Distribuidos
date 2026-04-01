from google import genai
from google.genai import types
import os


def agente_transcritor(video_url):
    # Limpeza da URL: Corta a string no primeiro '&' para remover &t=9s, &list=, etc.
    if "&" in video_url:
        video_url = video_url.split("&")[0]

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Erro: API Key do Gemini não configurada."

    try:
        client = genai.Client(api_key=api_key)
        modelo = "gemini-2.5-flash"
        
        prompt = """
        Você é um especialista em análise de mídia. 
        Por favor, transcreva todo o áudio falado neste vídeo de forma clara. 
        Descreva também as ações visuais mais importantes que ocorrem na tela.
        """
        
        response = client.models.generate_content(
            model=modelo,
            contents=[
                types.Part.from_uri(
                    file_uri=video_url,
                    mime_type="video/*" # Atualizado para o formato recomendado
                ),
                prompt
            ]
        )
        
        return response.text
        
    except Exception as e:
        return f"Erro na geração da inteligência artificial: {e}"



def agente_gerador_desafios(transcricao):
    """
    Recebe uma string com a transcrição de um vídeo e retorna 
    uma string em formato JSON com os desafios gerados.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        return "Erro: API Key do Gemini não configurada."

    try:
        client = genai.Client(api_key=api_key)
        # O modelo Flash continua sendo a melhor escolha para velocidade e JSON
        modelo = "gemini-2.5-flash"
        
        # O prompt foi ajustado para focar exclusivamente na leitura do texto
        prompt = """
        Você é um especialista em criar desafios educativos. 
        Leia a transcrição do vídeo fornecida e gere desafios de múltipla escolha com base no seu conteúdo. 
        Gere no máximo 15 desafios e no mínimo 10.
        Retorne estritamente uma lista de objetos JSON, onde cada objeto tenha as chaves: 
        'pergunta', 'opcoes' (uma lista com 4 strings) e 'resposta_correta'.
        """
        
        response = client.models.generate_content(
            model=modelo,
            contents=[
                prompt,
                f"TRANSCRIÇÃO DO VÍDEO:\n{transcricao}" # Injetamos a string recebida aqui
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        print(response.text)
        
        return response.text
        
    except Exception as e:
        return f"Erro na geração da inteligência artificial: {e}"
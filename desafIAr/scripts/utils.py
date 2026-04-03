import json
from desafIAr.models import Desafio, Video
from .agentes import agente_gerador_desafios
from urllib.parse import urlparse, parse_qs

def salvar_desafios_no_banco(video_id, transcricao):
    # 1. Chama a IA
    resultado_ia_string = agente_gerador_desafios(transcricao)
    
    # Verifica se não retornou um erro
    if resultado_ia_string.startswith("Erro"):
        print(resultado_ia_string)
        return False

    # 2. Converte a string JSON para uma lista de dicionários Python
    try:
        lista_desafios = json.loads(resultado_ia_string)
    except json.JSONDecodeError:
        print("Erro ao decodificar o JSON gerado pela IA.")
        return False

    # 3. Pega a instância do vídeo
    video_instancia = Video.objects.get(id=video_id)

    # 4. Salva cada desafio no banco de dados
    for item in lista_desafios:
        Desafio.objects.create(
            video=video_instancia,
            pergunta=item['pergunta'],
            opcoes=item['opcoes'], # O Django salva a lista direto graças ao JSONField
            resposta_correta=item['resposta_correta']
        )
        
    print(f"{len(lista_desafios)} desafios salvos com sucesso!")
    return True


def get_youtube_embed(url):
    parsed = urlparse(url)

    # Caso padrão: youtube.com/watch?v=
    if "youtube.com" in parsed.netloc:
        video_id = parse_qs(parsed.query).get("v")
        if video_id:
            return f"https://www.youtube.com/embed/{video_id[0]}"

    # Caso encurtado: youtu.be/
    if "youtu.be" in parsed.netloc:
        return f"https://www.youtube.com/embed{parsed.path}"

    return url  # fallback
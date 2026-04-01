import redis
import json
from celery import shared_task
from .models import Video, Desafio
from .scripts.agentes import agente_transcritor, agente_gerador_desafios
import logging
import time
import os

logger = logging.getLogger('desafIAr')

host_redis = os.environ.get('REDIS_HOST', 'redis')

cache = redis.Redis(host=host_redis, port=6379, db=0, decode_responses=True)

@shared_task
def processar_video_assincrono(video_id, video_url):
    # 1. IA processa o vídeo e devolve a string JSON
    transcricao = agente_transcritor(video_url)
    texto_transcrito = agente_gerador_desafios(transcricao)
    
    try:
        lista_desafios = json.loads(texto_transcrito)
    except json.JSONDecodeError:
        return "Erro: IA não retornou um JSON válido."

    # 2. REDIS PRIMEIRO: Disponibilidade imediata para o jogo!
    nome_fila = f"pool_desafios_video_{video_id}"
    for item in lista_desafios:
        # Empurra para a fila em memória (leva microssegundos)
        cache.lpush(nome_fila, json.dumps({
            'pergunta': item['pergunta'],
            'opcoes': item['opcoes'],
            'resposta_correta': item['resposta_correta']
        }))
    
    # --- A PARTIR DAQUI O FRONT-END JÁ CONSEGUE PUXAR AS PERGUNTAS ---
    
    # 3. POSTGRESQL DEPOIS: Grava no banco estático sem pressa
    video = Video.objects.get(id=video_id)
    video.transcricao = texto_transcrito
    video.save()
    
    for item in lista_desafios:
        Desafio.objects.create(
            video=video,
            pergunta=item['pergunta'],
            opcoes=item['opcoes'],
            resposta_correta=item['resposta_correta']
        )
        
    return f"Concluído: {len(lista_desafios)} desafios injetados no Redis e salvos no BD."
import json
import redis
from django.http import JsonResponse
from django.shortcuts import render
from .models import DesafioEstatico

from django.shortcuts import redirect
from .tasks import gerar_desafios_ia  # Importa a tarefa que criamos pro Celery

from django.shortcuts import render, redirect
from .tasks import gerar_desafios_ia  # Importamos a tarefa do Celery


# Configuração básica do Redis (garanta que o host bate com o docker-compose)
redis_client = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)

def home(request):
    return render(request, 'desafIAr/home.html')

def cadastrar_video(request):
    if request.method == 'POST':
        video_url = request.POST.get('video_url')
        
        # Extrai o ID do vídeo (ex: do YouTube) de forma simples para o teste
        video_id = video_url.split('v=')[-1].split('&')[0] if 'v=' in video_url else "video_generico"

        # DISPARO ASSÍNCRONO (Padrão POC 4)
        # O .delay() envia a tarefa para o Redis e o Worker assume.
        # A API (Django) fica livre imediatamente para atender outros usuários.
        gerar_desafios_ia.delay(video_id, f"Processando vídeo: {video_url}")

        contexto = {
            'mensagem': f'Sucesso! O vídeo {video_id} foi enviado para a fila de processamento da IA.'
        }
        return render(request, 'desafIAr/home.html', contexto)
    
    return redirect('home')


def cadastrar_video(request):
    if request.method == 'POST':
        video_url = request.POST.get('video_url')
        video_id = video_url.split('=')[-1] # Exemplo simples de extrair ID do YT

        # DISPARO ASSÍNCRONO: A API responde na hora, mas a IA trabalha no Worker
        # Isso atende ao padrão SYNC vs ASYNC exigido [cite: 92]
        gerar_desafios_ia.delay(video_id, f"Conteúdo do vídeo em {video_url}")

        return render(request, 'desafIAr/home.html', {'mensagem': 'Vídeo enviado! A IA está gerando os desafios no pool...'})
    return redirect('home')
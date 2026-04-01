from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
import re
import redis
import json
from .models import Video, Desafio
from .scripts.obter_titulo import obter_titulo_youtube
from .scripts.utils import get_youtube_embed
from .tasks import processar_video_assincrono
import os

# Conexão com o Redis
host_redis = os.environ.get('REDIS_HOST', 'redis')

cache = redis.Redis(host=host_redis, port=6379, db=0, decode_responses=True)

def home(request):
    return render(request, 'desafIAr/home.html')

def video_form(request):
    if request.method == 'POST':
        video_url_bruta = request.POST.get('video_url')

        # Limpeza da URL
        match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', video_url_bruta)
        if match:
            video_url = f"https://www.youtube.com/watch?v={match.group(1)}"
        else:
            video_url = video_url_bruta

        video_existente = Video.objects.filter(url=video_url).first()
        
        if video_existente:
            # Envia a mensagem de aviso
            messages.error(request, 'Este vídeo já está cadastrado no sistema!')
            # Redireciona diretamente para a página do vídeo que já existe
            return redirect('video_form')

        titulo = obter_titulo_youtube(video_url)
        
        # Cria o vídeo com status pendente
        novo_video = Video.objects.create(
            url=video_url,
            titulo=titulo,
            transcricao="A IA está a processar o vídeo em background. Os desafios ficarão disponíveis em breve!" 
        )
        
        # MÁGICA DO CELERY: Manda o trabalho pesado para background e liberta o servidor imediatamente
        processar_video_assincrono.delay(novo_video.id, video_url)
        
        return redirect('video_detail', pk=novo_video.id)
        
    return render(request, 'desafIAr/video_form.html')

def video_detail(request, pk=None):
    video = get_object_or_404(Video, pk=pk)
    url_embed = get_youtube_embed(video.url)
    
    context = {
        'video': video,
        'url_embed': url_embed
    }
    return render(request, 'desafIAr/video_detail.html', context)

def carregar_desafio(request, pk):
    nome_fila = f"pool_desafios_video_{pk}"
    # Pega os IDs que o front-end avisa que já mostrou
    ids_vistos = request.GET.getlist('vistos[]')
    
    # 1. TENTA CONSUMIR DO POOL (REDIS) PRIMEIRO - Latência Zero
    desafio_redis = cache.rpop(nome_fila)
    
    if desafio_redis:
        dados = json.loads(desafio_redis)
        dados['origem'] = 'Pool IA (Redis)'
        return JsonResponse(dados)
        
    # 2. FALLBACK NÍVEL 1: BANCO ESTÁTICO (Perguntas específicas do vídeo)
    desafio_banco = Desafio.objects.filter(video_id=pk).exclude(id__in=ids_vistos).order_by('?').first()
    
    if desafio_banco:
        return JsonResponse({
            'id': desafio_banco.id,
            'pergunta': desafio_banco.pergunta,
            'opcoes': desafio_banco.opcoes,
            'resposta_correta': desafio_banco.resposta_correta,
            'origem': '🗄️ Fallback (PostgreSQL - Específico)'
        })

    # 3. FALLBACK NÍVEL 2: BANCO ESTÁTICO (Perguntas Genéricas - video=null)
    # Busca apenas os desafios onde o vídeo não está preenchido
    desafio_generico = Desafio.objects.filter(video__isnull=True).exclude(id__in=ids_vistos).order_by('?').first()
    
    if desafio_generico:
        return JsonResponse({
            'id': desafio_generico.id,
            'pergunta': desafio_generico.pergunta,
            'opcoes': desafio_generico.opcoes,
            'resposta_correta': desafio_generico.resposta_correta,
            'origem': '🛡️ Fallback Extremo (PostgreSQL - Genérico)'
        })
        
    # 4. EXAUSTÃO TOTAL
    return JsonResponse({'erro': 'O sistema esgotou todas as perguntas possíveis!'}, status=404)

def video_list(request):
    videos = Video.objects.all()
    context = {'videos': videos}
    return render(request, 'desafIAr/video_list.html', context)
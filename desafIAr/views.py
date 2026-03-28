from django.shortcuts import render, redirect
from django.contrib import messages
import os
import json
from dotenv import load_dotenv
from .scripts.agentes import agente_transcritor, agente_gerador_desafios
from .scripts.obter_titulo import obter_titulo_youtube
from .models import Video, Desafio

def home(request):
    return render(request, 'desafIAr/home.html')


def video_form(request):
    if request.method == 'POST':
        video_url   = request.POST.get('video_url', '').strip()

        errors = {}

        if not video_url:
            errors['video_url'] = 'Informe o link do vídeo.'
        elif not (video_url.startswith('http://') or video_url.startswith('https://')):
            errors['video_url'] = 'Digite uma URL válida (ex: https://www.youtube.com/watch?v=...).'
        elif Video.objects.filter(url=video_url).exists():
            errors['video_url'] = 'Este vídeo já foi cadastrado.'

        if errors:
            context = {
                'errors': errors,
                'values': {
                    'video_url':   video_url,
                },
            }
            return render(request, 'desafIAr/video_form.html', context)
        
        titulo_oficial = obter_titulo_youtube(video_url)

        transcricao_video = agente_transcritor(video_url)

        agente_gerador_desafios(transcricao_video)

        video = Video.objects.create(
            url=video_url,
            titulo=titulo_oficial,
            transcricao=transcricao_video,
        )

        messages.success(
            request,
            f'Vídeo "{titulo_oficial}" cadastrado com sucesso! A IA já começou o processamento.'
        )

        return redirect('video_list')

    return render(request, 'desafIAr/video_form.html')

def video_detail(request, pk=None):
    video = Video.objects.get(pk=pk)
    context = {'video': video}
    return render(request, 'desafIAr/video_detail.html', context)

def video_list(request):
    videos = Video.objects.all()
    context = {'videos': videos}
    return render(request, 'desafIAr/video_list.html', context)
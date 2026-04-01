from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
import os
import re
import json
from dotenv import load_dotenv
from .scripts.agentes import agente_transcritor, agente_gerador_desafios
from .scripts.obter_titulo import obter_titulo_youtube
from .scripts.utils import salvar_desafios_no_banco, get_youtube_embed
from .models import Video, Desafio
from django.http import JsonResponse

def home(request):
    return render(request, 'desafIAr/home.html')


def video_form(request):
    if request.method == 'POST':
        video_url_bruta = request.POST.get('video_url')

        # 1. LIMPEZA DA URL (Extrai o ID de 11 caracteres do YouTube)
        match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', video_url_bruta)
        if match:
            video_id = match.group(1)
            # Reconstrói a URL no formato mais limpo possível
            video_url = f"https://www.youtube.com/watch?v={video_id}"
        else:
            video_url = video_url_bruta # Fallback caso o Regex falhe

        titulo = obter_titulo_youtube(video_url)
        
        # 1. SALVA O VÍDEO PRIMEIRO
        # Cria o registro no banco para gerar o ID. A transcrição fica vazia ou com um aviso temporário.
        novo_video = Video.objects.create(
            url=video_url,
            titulo=titulo,
            transcricao="Processando transcrição..." 
        )
        
        # 2. RODA O AGENTE TRANSCRITOR
        # A IA assiste ao vídeo e devolve o texto
        texto_transcrito = agente_transcritor(video_url)
        
        # 3. ATUALIZA O BANCO COM A TRANSCRIÇÃO REAL
        novo_video.transcricao = texto_transcrito
        novo_video.save()
        
        # 4. GERA OS DESAFIOS
        # Agora passamos o ID numérico correto e a transcrição finalizada
        salvar_desafios_no_banco(novo_video.id, novo_video.transcricao)
        
        # 5. REDIRECIONA PARA A TELA DO VÍDEO
        return redirect('video_detail', pk=novo_video.id)
        
    return render(request, 'desafIAr/video_form.html')


def video_detail(request, pk=None):
    video = get_object_or_404(Video, pk=pk)
    
    # Para o YouTube rodar no site, a URL precisa ter '/embed/' em vez de '/watch?v='
    # Ex: https://www.youtube.com/embed/SEU_ID
    url_embed = get_youtube_embed(video.url)

    print("esta é a url:", url_embed)
    
    context = {
        'video': video,
        'url_embed': url_embed
    }
    return render(request, 'desafIAr/video_detail.html', context)

# View para o AJAX (Não recarrega a página)
def carregar_desafio(request, pk):
    # Pega um desafio aleatório deste vídeo do banco estático (Seu Fallback)
    # Na POC final, você vai dar um 'rpop' no Redis aqui antes de ir pro banco!
    desafio = Desafio.objects.filter(video_id=pk).order_by('?').first()
    
    if desafio:
        return JsonResponse({
            'pergunta': desafio.pergunta,
            'opcoes': desafio.opcoes, # Retorna a lista de 4 strings nativamente
            'resposta_correta': desafio.resposta_correta
        })
    else:
        return JsonResponse({'erro': 'Nenhum desafio no pool'}, status=404)


def video_list(request):
    videos = Video.objects.all()
    context = {'videos': videos}
    return render(request, 'desafIAr/video_list.html', context)
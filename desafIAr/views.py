from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Video

def home(request):
    return render(request, 'desafIAr/home.html')


def video_form(request):
    if request.method == 'POST':
        video_url   = request.POST.get('video_url', '').strip()
        titulo       = request.POST.get('titulo', '').strip()

        errors = {}

        if not video_url:
            errors['video_url'] = 'Informe o link do vídeo.'
        elif not (video_url.startswith('http://') or video_url.startswith('https://')):
            errors['video_url'] = 'Digite uma URL válida (ex: https://www.youtube.com/watch?v=...).'

        if errors:
            context = {
                'errors': errors,
                'values': {
                    'video_url':   video_url,
                    'titulo':       titulo,
                },
            }
            return render(request, 'desafIAr/video_form.html', context)
        
        video = Video.objects.create(
            url=video_url,
            titulo=titulo,
        )

        video.save()

        messages.success(
            request,
            f'Vídeo "{titulo or video_url}" cadastrado com sucesso! A IA já começou o processamento.'
        )

        return redirect('video_list')

    return render(request, 'desafIAr/video_form.html')

def video_detail(request, pk=None):
    context = {}
    return render(request, 'desafIAr/video_detail.html', context)

def video_list(request):
    videos = Video.objects.all()
    context = {'videos': videos}
    return render(request, 'desafIAr/video_list.html', context)
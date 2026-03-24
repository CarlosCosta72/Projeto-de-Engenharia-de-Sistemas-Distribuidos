import json
import redis
from django.http import JsonResponse
from django.shortcuts import render
from .models import DesafioEstatico

# Configuração básica do Redis (garanta que o host bate com o docker-compose)
redis_client = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)

def home(request):
    return render(request, 'desafIAr/home.html')

def obter_desafios(request, video_id):
    """ API que aplica o padrão Cache-Aside e Fallback """
    
    # 1. Tenta buscar no Redis (Pool alimentado pela IA)
    try:
        desafios_cacheados = redis_client.get(f"pool_video_{video_id}")
        if desafios_cacheados:
            return JsonResponse({
                "origem": "IA_ASSINCRONA (Redis)", 
                "desafios": json.loads(desafios_cacheados)
            })
    except redis.ConnectionError:
        pass # Se o Redis estiver fora do ar, ignora e vai para o banco estático

    # 2. Fallback: Disjuntor aberto ou Pool vazio -> Busca no PostgreSQL
    desafios_banco = DesafioEstatico.objects.filter(video_id=video_id)
    
    if desafios_banco.exists():
        lista_desafios = list(desafios_banco.values('pergunta', 'resposta_correta', 'alternativas'))
        return JsonResponse({
            "origem": "FALLBACK_ESTATICO (PostgreSQL)", 
            "desafios": lista_desafios
        })

    return JsonResponse({"erro": "Nenhum desafio encontrado no Pool e Banco estático vazio."}, status=404)
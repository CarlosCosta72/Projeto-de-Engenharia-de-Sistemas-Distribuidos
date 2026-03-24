import os
import json
import redis
import requests
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

# Conexão com o Redis (Message Broker e Cache)
redis_client = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)

# Configurações do Circuit Breaker
FAIL_THRESHOLD = 3      # Quantas falhas seguidas abrem o disjuntor
CB_TIMEOUT = 60         # Tempo em segundos que o disjuntor fica aberto (Cooldown)

@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def gerar_desafios_ia(self, video_id, contexto_video):
    """
    Tarefa ASYNC para bater na LLM e encher o pool.
    Implementa os padrões: Queues, Circuit Breaker e Retry Pattern.
    """
    
    # 1. VERIFICAÇÃO DO CIRCUIT BREAKER
    cb_state = redis_client.get("ia_circuit_breaker_state")
    if cb_state == "OPEN":
        return f"Abortado: Circuit Breaker está ABERTO. Sistema operando via Fallback."

    # 2. PREPARAÇÃO DA CHAMADA À IA
    api_key = os.getenv("OPENROUTER_API_KEY")
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "meta-llama/llama-3.2-3b-instruct:free",
        "messages": [
            {"role": "system", "content": "Você é um gerador de quizzes. Retorne APENAS um JSON válido com uma lista de 5 desafios sobre o tema fornecido. Formato: [{'pergunta': '...', 'resposta_correta': '...', 'alternativas': [...]}]"},
            {"role": "user", "content": f"Gere desafios para o seguinte contexto de vídeo: {contexto_video}"}
        ]
    }

    # 3. EXECUÇÃO COM PROTEÇÃO (Try/Except)
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status() # Lança erro se status não for 2xx
        
        resultado = response.json()
        desafios_gerados = resultado['choices'][0]['message']['content']
        
        # Opcional: Validar se o retorno é realmente um JSON
        json_valido = json.loads(desafios_gerados)
        
        # 4. SUCESSO: Alimenta o Pool e reseta o Circuit Breaker
        redis_client.set(f"pool_video_{video_id}", json.dumps(json_valido), ex=3600) # Expira em 1 hora
        redis_client.set("ia_fail_count", 0) # Reseta as falhas
        
        return f"Sucesso! Pool do vídeo {video_id} abastecido com {len(json_valido)} desafios."

    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        # 5. FALHA: Incrementa erros e aciona Circuit Breaker se necessário
        falhas_atuais = redis_client.incr("ia_fail_count")
        
        if falhas_atuais >= FAIL_THRESHOLD:
            # Abre o disjuntor e define o tempo de cooldown
            redis_client.set("ia_circuit_breaker_state", "OPEN", ex=CB_TIMEOUT)
            redis_client.set("ia_fail_count", 0) # Reseta contagem para a próxima janela
            print(f"CRÍTICO: Circuit Breaker ABERTO após {falhas_atuais} falhas. Motivo: {str(e)}")
        
        # Tenta novamente (Retry Pattern) até o max_retries
        try:
            raise self.retry(exc=e)
        except MaxRetriesExceededError:
            return "Falha definitiva após várias tentativas. Desistindo."
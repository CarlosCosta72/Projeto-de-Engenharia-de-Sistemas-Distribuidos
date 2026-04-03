from locust import HttpUser, task, between
import random

class DesafIArLoadTest(HttpUser):
    # Simula um usuário que clica nas coisas e lê a tela (espera de 1 a 3 segundos entre ações)
    wait_time = between(1, 3)

    @task(3)
    def carregar_desafio(self):
        """
        Simula o consumo da API (Peso 3: ocorre 3x mais vezes que o envio de vídeos).
        Testa a rota de fallback (Redis -> Postgres -> 404).
        """
        # Sorteia um ID de vídeo entre 1 e 10 (ajuste conforme o seu banco de dados de teste)
        video_id = random.randint(1, 10)
        
        with self.client.get(f"/api/video/{video_id}/desafio/", catch_response=True) as response:
            # Se retornar 200 (achou desafio) ou 404 (esgotou), consideramos comportamento normal do sistema
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Erro inesperado na API: {response.status_code}")
from django.db import models

class DesafioEstatico(models.Model):
    video_id = models.CharField(max_length=100, help_text="ID ou título do vídeo")
    pergunta = models.TextField()
    resposta_correta = models.CharField(max_length=255)
    alternativas = models.JSONField(help_text="Lista de alternativas em JSON")

    def __str__(self):
        return f"{self.video_id} - {self.pergunta[:30]}..."
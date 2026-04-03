from django.db import models

# Create your models here.
class Video(models.Model):
    titulo = models.CharField(max_length=100)
    transcricao = models.TextField()
    url = models.URLField()
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.titulo



class Desafio(models.Model):
    video = models.ForeignKey('Video', on_delete=models.CASCADE, related_name='desafios', null=True, blank=True)
    
    # Novos campos mapeados diretamente do JSON da IA
    pergunta = models.TextField()
    opcoes = models.JSONField()  # Salvará a lista de 4 strings perfeitamente
    resposta_correta = models.CharField(max_length=255)
    
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        # Mostra os primeiros 50 caracteres da pergunta no painel Admin
        return f"{self.pergunta[:50]}..."
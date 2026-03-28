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
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='desafios', null=True, blank=True)
    titulo = models.CharField(max_length=100)
    descricao = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.titulo
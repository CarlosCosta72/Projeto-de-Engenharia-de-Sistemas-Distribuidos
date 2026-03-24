from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('cadastrar/', views.cadastrar_video, name='cadastrar_video'), # Nova Rota
    path('obter-desafios/<str:video_id>/', views.obter_desafios, name='obter_desafios'),
]
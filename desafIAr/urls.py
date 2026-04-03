from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('novo/', views.video_form, name='video_form'), 
    path('video/', views.video_detail, name='video_detail'),
    path('lista/', views.video_list, name='video_list'),
    path('video/<int:pk>/', views.video_detail, name='video_detail'),
    path('api/video/<int:pk>/desafio/', views.carregar_desafio, name='api_carregar_desafio'),
]
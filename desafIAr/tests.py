import json
from unittest.mock import patch, MagicMock
import logging

from django.test import TestCase, Client
from django.urls import reverse

from .models import Video, Desafio
from .scripts.utils import get_youtube_embed
from .scripts.obter_titulo import obter_titulo_youtube
from .tasks import processar_video_assincrono


class ModelsTests(TestCase):
    def test_video_str_returns_title(self):
        video = Video.objects.create(
            titulo="Teste 1",
            url="https://www.youtube.com/watch?v=abc123def45",
            transcricao="transcricao"
        )
        self.assertEqual(str(video), "Teste 1")

    def test_desafio_str_contains_question_snippet(self):
        desafio = Desafio.objects.create(
            video=None,
            pergunta="Uma pergunta muito longa para testar o __str__ do modelo",
            opcoes=["A", "B", "C", "D"],
            resposta_correta="A"
        )
        self.assertTrue(str(desafio).startswith("Uma pergunta muito longa"))


class UtilTests(TestCase):
    def test_get_youtube_embed_full_url(self):
        embed = get_youtube_embed("https://www.youtube.com/watch?v=abc123def45")
        self.assertEqual(embed, "https://www.youtube.com/embed/abc123def45")

    def test_get_youtube_embed_short_url(self):
        embed = get_youtube_embed("https://youtu.be/abc123def45")
        self.assertEqual(embed, "https://www.youtube.com/embed/abc123def45")

    def test_get_youtube_embed_unknown_url(self):
        embed = get_youtube_embed("https://example.com/test")
        self.assertEqual(embed, "https://example.com/test")

    @patch("desafIAr.scripts.obter_titulo.requests.get")
    def test_obter_titulo_youtube_success(self, mock_get):
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {"title": "Vídeo de teste"}
        mock_get.return_value = mock_response

        titulo = obter_titulo_youtube("https://www.youtube.com/watch?v=abc123def45")
        self.assertEqual(titulo, "Vídeo de teste")

    @patch("builtins.print")
    @patch("desafIAr.scripts.obter_titulo.requests.get")
    def test_obter_titulo_youtube_failure(self, mock_get, mock_print): # <-- O detalhe está aqui na adição do mock_print!
        mock_get.side_effect = Exception("Rede indisponível")
        titulo = obter_titulo_youtube("https://www.youtube.com/watch?v=abc123def45")
        self.assertEqual(titulo, "Vídeo em Processamento")


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        logging.getLogger('django.request').setLevel(logging.ERROR)

    @patch("desafIAr.views.obter_titulo_youtube", return_value="Título mock")
    @patch("desafIAr.views.processar_video_assincrono")
    def test_video_form_creates_video_and_dispatches_task(self, mock_task, mock_obter_titulo):
        response = self.client.post(
            reverse("video_form"),
            data={"video_url": "https://www.youtube.com/watch?v=test123456"}
        )

        self.assertEqual(Video.objects.count(), 1)
        video = Video.objects.first()
        self.assertEqual(video.titulo, "Título mock")
        mock_task.delay.assert_called_once_with(video.id, video.url)
        self.assertEqual(response.status_code, 302)

    @patch("desafIAr.views.obter_titulo_youtube", return_value="Título mock")
    @patch("desafIAr.views.processar_video_assincrono")
    def test_video_form_duplicate_redirects_back(self, mock_task, mock_obter_titulo):
        Video.objects.create(
            titulo="Título mock",
            url="https://www.youtube.com/watch?v=test123456",
            transcricao="x"
        )

        response = self.client.post(
            reverse("video_form"),
            data={"video_url": "https://www.youtube.com/watch?v=test123456"}
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Video.objects.count(), 1)
        mock_task.delay.assert_not_called()

    @patch("desafIAr.views.cache")
    def test_carregar_desafio_redis_pool(self, mock_cache):
        video = Video.objects.create(
            titulo="Título",
            url="https://www.youtube.com/watch?v=abc123def45",
            transcricao="teste"
        )
        payload = {
            "pergunta": "Pergunta Redis",
            "opcoes": ["A", "B", "C", "D"],
            "resposta_correta": "A"
        }
        mock_cache.rpop.return_value = json.dumps(payload)

        response = self.client.get(reverse("api_carregar_desafio", kwargs={"pk": video.id}))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["pergunta"], "Pergunta Redis")
        self.assertEqual(data["origem"], "Pool IA (Redis)")

    def test_carregar_desafio_postgres_video_fallback(self):
        video = Video.objects.create(
            titulo="Título",
            url="https://www.youtube.com/watch?v=abc123def45",
            transcricao="teste"
        )
        desafio = Desafio.objects.create(
            video=video,
            pergunta="Pergunta DB",
            opcoes=["A", "B", "C", "D"],
            resposta_correta="B"
        )

        response = self.client.get(reverse("api_carregar_desafio", kwargs={"pk": video.id}))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], desafio.id)
        self.assertIn("Fallback", data["origem"])

    def test_carregar_desafio_postgres_generic_fallback(self):
        generic = Desafio.objects.create(
            video=None,
            pergunta="Pergunta Genérica",
            opcoes=["A", "B", "C", "D"],
            resposta_correta="C"
        )
        video = Video.objects.create(
            titulo="Título",
            url="https://www.youtube.com/watch?v=abc123def45",
            transcricao="teste"
        )

        response = self.client.get(reverse("api_carregar_desafio", kwargs={"pk": video.id}))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], generic.id)
        self.assertIn("Fallback Extremo", data["origem"])

    def test_carregar_desafio_exhausted_returns_404(self):
        video = Video.objects.create(
            titulo="Título",
            url="https://www.youtube.com/watch?v=abc123def45",
            transcricao="teste"
        )

        response = self.client.get(reverse("api_carregar_desafio", kwargs={"pk": video.id}))
        self.assertEqual(response.status_code, 404)


class TaskTests(TestCase):
    @patch("desafIAr.tasks.agente_transcritor", return_value="texto transcrito")
    @patch("desafIAr.tasks.agente_gerador_desafios")
    @patch("desafIAr.tasks.cache")
    def test_processar_video_assincrono_happy_path(self, mock_cache, mock_gerador, mock_transcritor):
        video = Video.objects.create(
            titulo="Título",
            url="https://www.youtube.com/watch?v=abc123def45",
            transcricao="Pendente"
        )

        desafios = [
            {"pergunta": "Q1", "opcoes": ["A", "B", "C", "D"], "resposta_correta": "A"},
            {"pergunta": "Q2", "opcoes": ["A", "B", "C", "D"], "resposta_correta": "B"}
        ]
        mock_gerador.return_value = json.dumps(desafios)

        resposta = processar_video_assincrono(video.id, video.url)

        self.assertIn("Concluído", resposta)
        self.assertEqual(mock_cache.lpush.call_count, 2)
        self.assertEqual(Desafio.objects.filter(video=video).count(), 2)

        video.refresh_from_db()
        self.assertEqual(video.transcricao, json.dumps(desafios))

    @patch("desafIAr.tasks.agente_transcritor", return_value="texto transcrito")
    @patch("desafIAr.tasks.agente_gerador_desafios", return_value="not-json")
    @patch("desafIAr.tasks.cache")
    def test_processar_video_assincrono_invalid_json(self, mock_cache, mock_gerador, mock_transcritor):
        video = Video.objects.create(
            titulo="Título",
            url="https://www.youtube.com/watch?v=abc123def45",
            transcricao="Pendente"
        )

        resposta = processar_video_assincrono(video.id, video.url)

        self.assertEqual(resposta, "Erro: IA não retornou um JSON válido.")
        self.assertEqual(Desafio.objects.filter(video=video).count(), 0)

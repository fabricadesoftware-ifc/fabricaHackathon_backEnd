from datetime import date, timedelta
from io import BytesIO
from unittest import mock

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from .models import Apoiador, Edicao, Equipe, Projeto, Tema, TipoEdicao, User
from .models.user import tipoUser
from .validations import imagem_validation

STORAGE_MEMORIA = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


def imagem(formato="PNG", nome="foto.png", tamanho=(4, 4)):
    buffer = BytesIO()
    Image.new("RGB", tamanho, "red").save(buffer, format=formato)
    return SimpleUploadedFile(nome, buffer.getvalue(), content_type=f"image/{formato.lower()}")


@override_settings(STORAGES=STORAGE_MEMORIA)
class ImagensTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        mk = User.objects.create_user
        self.admin = mk(username="adm", email="adm@t.com", password="x", tipoUser=tipoUser.admin)
        self.part = mk(username="part", email="part@t.com", password="x", tipoUser=tipoUser.participante)
        self.part2 = mk(username="part2", email="part2@t.com", password="x", tipoUser=tipoUser.participante)
        tipo = TipoEdicao.objects.create(nome="Presencial")
        self.edicao = Edicao.objects.create(
            nome="Hack", ano=2026, status="INSCRICAO",
            data_inicio=date.today(), data_fim=date.today() + timedelta(days=3),
            minimo_participantes=2, maximo_participantes=5, maximo_equipes=10,
            tipo_edicao=tipo,
        )
        self.apoiador = Apoiador.objects.create(nome="Apoio", tipo="ouro")
        self.projeto = Projeto.objects.create(nome_projeto="P", descricao_projeto="D", edicao=self.edicao)

    def as_user(self, user):
        self.client.force_authenticate(user=user)
        return self.client


class UploadTests(ImagensTestCase):
    def test_upload_capa_devolve_url_absoluta(self):
        resp = self.as_user(self.admin).patch(
            f"/api/edicoes/{self.edicao.id}/", {"imagem_capa": imagem()}, format="multipart"
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertTrue(resp.data["imagem_capa"].startswith("http://testserver/"))
        self.edicao.refresh_from_db()
        self.assertTrue(self.edicao.imagem_capa.name.startswith("hackathon/edicoes/"))
        self.assertTrue(default_storage.exists(self.edicao.imagem_capa.name))

    def test_upload_logo_apoiador_e_projeto(self):
        resp = self.as_user(self.admin).patch(
            f"/api/apoiadores/{self.apoiador.id}/", {"logo_apoiador": imagem(nome="a.png")}, format="multipart"
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertTrue(resp.data["logo_apoiador"].startswith("http"))
        resp = self.as_user(self.admin).patch(
            f"/api/projetos/{self.projeto.id}/",
            {"logo_projeto": imagem("WEBP", "p.webp")}, format="multipart",
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertTrue(resp.data["logo_projeto"].startswith("http"))

    def test_jpeg_aceito_no_post_de_apoiador(self):
        resp = self.as_user(self.admin).post(
            "/api/apoiadores/",
            {"nome": "Novo", "tipo": "prata", "logo_apoiador": imagem("JPEG", "l.jpg")},
            format="multipart",
        )
        self.assertEqual(resp.status_code, 201, resp.content)

    def test_usuario_altera_propria_foto(self):
        resp = self.as_user(self.part).patch(
            f"/api/users/{self.part.id}/", {"foto_perfil": imagem()}, format="multipart"
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertTrue(resp.data["foto_perfil"].startswith("http://testserver/"))

    def test_sem_imagem_devolve_null(self):
        resp = self.client.get(f"/api/apoiadores/{self.apoiador.id}/")
        self.assertIsNone(resp.data["logo_apoiador"])
        resp = self.client.get(f"/api/edicoes/{self.edicao.id}/")
        self.assertIsNone(resp.data["imagem_capa"])


class ValidacaoTests(ImagensTestCase):
    def patch_capa(self, arquivo):
        return self.as_user(self.admin).patch(
            f"/api/edicoes/{self.edicao.id}/", {"imagem_capa": arquivo}, format="multipart"
        )

    def test_tipo_invalido_400(self):
        resp = self.patch_capa(imagem("GIF", "a.gif"))
        self.assertEqual(resp.status_code, 400)
        self.assertIn("imagem_capa", resp.data)

    def test_conteudo_nao_imagem_com_extensao_png_400(self):
        falso = SimpleUploadedFile("falso.png", b"isto nao e uma imagem", content_type="image/png")
        self.assertEqual(self.patch_capa(falso).status_code, 400)

    def test_arquivo_grande_400(self):
        with mock.patch.object(imagem_validation, "IMAGEM_TAMANHO_MAXIMO", 100):
            resp = self.patch_capa(imagem(tamanho=(200, 200)))
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tamanho máximo", str(resp.data["imagem_capa"]))


class LimpezaTests(ImagensTestCase):
    def test_remover_com_null_apaga_arquivo(self):
        client = self.as_user(self.admin)
        client.patch(f"/api/edicoes/{self.edicao.id}/", {"imagem_capa": imagem()}, format="multipart")
        self.edicao.refresh_from_db()
        nome = self.edicao.imagem_capa.name
        resp = client.patch(f"/api/edicoes/{self.edicao.id}/", {"imagem_capa": None}, format="json")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertIsNone(resp.data["imagem_capa"])
        self.assertFalse(default_storage.exists(nome))

    def test_substituir_apaga_a_anterior(self):
        client = self.as_user(self.admin)
        client.patch(f"/api/apoiadores/{self.apoiador.id}/", {"logo_apoiador": imagem(nome="a.png")}, format="multipart")
        self.apoiador.refresh_from_db()
        antigo = self.apoiador.logo_apoiador.name
        resp = client.patch(
            f"/api/apoiadores/{self.apoiador.id}/", {"logo_apoiador": imagem(nome="b.png")}, format="multipart"
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        self.apoiador.refresh_from_db()
        self.assertNotEqual(self.apoiador.logo_apoiador.name, antigo)
        self.assertFalse(default_storage.exists(antigo))
        self.assertTrue(default_storage.exists(self.apoiador.logo_apoiador.name))

    def test_falha_ao_apagar_nao_derruba_requisicao(self):
        client = self.as_user(self.admin)
        client.patch(f"/api/apoiadores/{self.apoiador.id}/", {"logo_apoiador": imagem(nome="a.png")}, format="multipart")
        with mock.patch.object(type(default_storage._wrapped), "delete", side_effect=RuntimeError("rede")):
            with self.assertLogs("core.hackathon.serializers.imagem", level="ERROR"):
                resp = client.patch(
                    f"/api/apoiadores/{self.apoiador.id}/", {"logo_apoiador": None}, format="json"
                )
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertIsNone(resp.data["logo_apoiador"])

    def test_atualizar_outro_campo_preserva_imagem(self):
        client = self.as_user(self.admin)
        client.patch(f"/api/apoiadores/{self.apoiador.id}/", {"logo_apoiador": imagem()}, format="multipart")
        self.apoiador.refresh_from_db()
        nome = self.apoiador.logo_apoiador.name
        client.patch(f"/api/apoiadores/{self.apoiador.id}/", {"nome": "Outro"}, format="json")
        self.assertTrue(default_storage.exists(nome))


class PermissaoEPrivacidadeTests(ImagensTestCase):
    def test_participante_nao_envia_capa_nem_logo(self):
        client = self.as_user(self.part)
        r = client.patch(f"/api/edicoes/{self.edicao.id}/", {"imagem_capa": imagem()}, format="multipart")
        self.assertEqual(r.status_code, 403)
        r = client.patch(f"/api/apoiadores/{self.apoiador.id}/", {"logo_apoiador": imagem()}, format="multipart")
        self.assertEqual(r.status_code, 403)
        r = client.patch(f"/api/projetos/{self.projeto.id}/", {"logo_projeto": imagem()}, format="multipart")
        self.assertEqual(r.status_code, 403)

    def test_usuario_nao_altera_foto_de_outro(self):
        resp = self.as_user(self.part).patch(
            f"/api/users/{self.part2.id}/", {"foto_perfil": imagem()}, format="multipart"
        )
        self.assertEqual(resp.status_code, 403)

    def test_anonimo_nao_envia(self):
        self.client.force_authenticate(user=None)
        r = self.client.patch(f"/api/edicoes/{self.edicao.id}/", {"imagem_capa": imagem()}, format="multipart")
        self.assertEqual(r.status_code, 401)

    def test_respostas_publicas_nao_expoem_foto_perfil(self):
        equipe_tema = Tema.objects.create(descricao_tema="T", edicao=self.edicao)
        Equipe.objects.create(nome_equipe="E", edicao=self.edicao, tema=equipe_tema, projeto=self.projeto)
        self.as_user(self.part).patch(
            f"/api/users/{self.part.id}/", {"foto_perfil": imagem()}, format="multipart"
        )
        self.client.force_authenticate(user=None)
        for url in (
            "/api/edicoes/", f"/api/edicoes/{self.edicao.id}/", "/api/apoiadores/",
            "/api/projetos/", f"/api/projetos/{self.projeto.id}/", "/api/equipes/",
        ):
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200, url)
            self.assertNotIn("foto_perfil", resp.content.decode(), url)

    def test_campos_de_imagem_nas_respostas_publicas(self):
        self.as_user(self.admin).patch(
            f"/api/projetos/{self.projeto.id}/", {"logo_projeto": imagem()}, format="multipart"
        )
        self.client.force_authenticate(user=None)
        detalhe = self.client.get(f"/api/edicoes/{self.edicao.id}/").data
        self.assertIn("imagem_capa", detalhe)
        self.assertIn("logo_apoiador", self.client.get("/api/apoiadores/").data["results"][0])
        projeto = self.client.get(f"/api/projetos/{self.projeto.id}/").data
        self.assertTrue(projeto["logo_projeto"].startswith("http"))


class SemCloudinaryTests(TestCase):
    def test_sem_cloudinary_url_usa_filesystem(self):
        self.assertNotIn("CLOUDINARY_URL", __import__("os").environ)
        self.assertEqual(
            settings.STORAGES["default"]["BACKEND"], "django.core.files.storage.FileSystemStorage"
        )

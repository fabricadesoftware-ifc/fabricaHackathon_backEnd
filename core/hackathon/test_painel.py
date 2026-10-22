from .models import AvaliadorEdicao, Criterio, Nota
from .services.nota_final import recalcular_nota_final
from .test_regras_negocio import Base


class PainelAdminTest(Base):
    def setUp(self):
        super().setUp()
        self.equipe = self.criar_equipe("Alfa", self.u1, (self.u2,))
        self.projeto = self.equipe.projeto
        self.crit = Criterio.objects.create(nome="Inovação", edicao=self.edicao)

    def get(self, user, url):
        return self.as_user(user).get(url)

    def test_somente_admin(self):
        for u in (self.prof, self.aval, self.u1):
            self.assertEqual(self.get(u, "/api/painel/edicoes/").status_code, 403)
            self.assertEqual(self.get(u, f"/api/painel/edicoes/{self.edicao.id}/").status_code, 403)
        self.client.logout()
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get("/api/painel/edicoes/").status_code, 401)

    def test_lista_resumo_e_equipes(self):
        r = self.get(self.admin, "/api/painel/edicoes/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data[0]["contagens"]["equipes"], 1)
        r = self.get(self.admin, f"/api/painel/edicoes/{self.edicao.id}/")
        self.assertEqual(r.data["contagens"]["participantes"], 2)
        self.assertEqual(len(r.data["criterios"]), 1)
        r = self.get(self.admin, f"/api/painel/edicoes/{self.edicao.id}/equipes/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data[0]["membros"]), 2)
        self.assertFalse(r.data[0]["pre_avaliacao"]["preenchida"])

    def test_vincular_e_desvincular_avaliador(self):
        base = f"/api/painel/edicoes/{self.edicao.id}/avaliadores/"
        c = self.as_user(self.admin)
        r = c.get(base)
        self.assertEqual({x["user_id"] for x in r.data}, {self.aval.id, self.aval2.id})
        self.assertTrue(all(not x["vinculado"] for x in r.data))
        self.assertEqual(c.post(base, {"user": self.aval.id}, format="json").status_code, 201)
        self.assertEqual(c.post(base, {"user": self.aval.id}, format="json").status_code, 200)
        self.assertEqual(c.post(base, {"user": self.u1.id}, format="json").status_code, 400)
        self.assertTrue(next(x for x in c.get(base).data if x["user_id"] == self.aval.id)["vinculado"])
        self.assertEqual(c.delete(f"{base}{self.aval.id}/").status_code, 204)
        self.assertFalse(AvaliadorEdicao.objects.exists())

    def test_nao_desvincula_com_notas_e_resultados(self):
        v = AvaliadorEdicao.objects.create(avaliador=self.aval, edicao=self.edicao)
        Nota.objects.create(nota=8, projeto=self.projeto, criterio=self.crit, avaliador=v)
        recalcular_nota_final(self.projeto)
        c = self.as_user(self.admin)
        r = c.delete(f"/api/painel/edicoes/{self.edicao.id}/avaliadores/{self.aval.id}/")
        self.assertEqual(r.status_code, 400)
        r = c.get(f"/api/painel/edicoes/{self.edicao.id}/resultados/")
        self.assertEqual(r.status_code, 200)
        linha = r.data["resultados"][0]
        self.assertEqual(linha["por_criterio"][0]["media"], "8.00")
        self.assertTrue(linha["completo"])
        self.assertEqual(linha["posicao"], 1)


class FalhaStorageTest(Base):
    def test_falha_no_storage_vira_400(self):
        from io import BytesIO
        from unittest import mock

        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image

        buf = BytesIO()
        Image.new("RGB", (10, 10)).save(buf, "PNG")
        foto = SimpleUploadedFile("f.png", buf.getvalue(), content_type="image/png")
        with mock.patch("django.core.files.storage.FileSystemStorage._save", side_effect=RuntimeError("cloud off")):
            r = self.as_user(self.u1).patch("/api/me/", {"first_name": "Ana", "foto_perfil": foto}, format="multipart")
        self.assertEqual(r.status_code, 400)
        self.assertIn("foto_perfil", r.data)

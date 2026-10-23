from django.core import mail
from django.test import override_settings

from .models import ConviteEquipe, ParticipanteEquipe
from .test_regras_negocio import Base


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", FRONTEND_URL="https://front.test")
class ConviteEquipeTest(Base):
    def setUp(self):
        super().setUp()
        self.equipe = self.criar_equipe("Alfa", self.u1)
        self.url = f"/api/inscricoes/{self.equipe.id}/"

    def test_email_sem_conta_vira_convite_enviado(self):
        c = self.as_user(self.u1)
        r = c.post(self.url + "membros/", {"membros": ["novo@t.com", "u2@t.com"]}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual([m["email"] for m in r.json()["membros"]], ["u1@t.com", "u2@t.com"])
        convites = r.json()["convites"]
        self.assertEqual(len(convites), 1)
        self.assertEqual((convites[0]["email"], convites[0]["status"], convites[0]["email_enviado"]), ("novo@t.com", "PENDENTE", True))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("https://front.test/convite/", mail.outbox[0].body)
        # repetir o mesmo e-mail é recusado
        r = c.post(self.url + "membros/", {"membros": ["novo@t.com"]}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_falha_de_email_nao_derruba(self):
        from unittest import mock
        with mock.patch("core.hackathon.services.convites.send_mail", side_effect=OSError("smtp off")):
            r = self.as_user(self.u1).post(self.url + "membros/", {"membros": ["novo@t.com"]}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["convites"][0]["email_enviado"])

    def test_convites_contam_para_o_maximo(self):
        c = self.as_user(self.u1)  # máximo 3 (criador + 2)
        self.assertEqual(c.post(self.url + "membros/", {"membros": ["a@t.com", "b@t.com"]}, format="json").status_code, 200)
        self.assertEqual(c.post(self.url + "membros/", {"membros": ["c@t.com"]}, format="json").status_code, 400)

    def test_aceitar_convite_por_email(self):
        self.as_user(self.u1).post(self.url + "membros/", {"membros": ["novo@t.com"]}, format="json")
        token = ConviteEquipe.objects.get(email="novo@t.com").token
        info = self.client.get(f"/api/convites/{token}/")  # público
        self.client.force_authenticate(user=None)
        info = self.client.get(f"/api/convites/{token}/")
        self.assertEqual(info.status_code, 200)
        self.assertTrue(info.json()["valido"])
        self.assertEqual(info.json()["equipe"], "Alfa")
        r = self.as_user(self.u3).post(f"/api/convites/{token}/aceitar/")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(ParticipanteEquipe.objects.filter(user=self.u3, equipe=self.equipe).exists())
        self.assertEqual(ConviteEquipe.objects.get(email="novo@t.com").status, "ACEITO")
        # usado: não vale de novo
        self.assertEqual(self.as_user(self.u4).post(f"/api/convites/{token}/aceitar/").status_code, 400)

    def test_link_reutilizavel_ate_lotar(self):
        c = self.as_user(self.u1)
        r = c.post(self.url + "link-convite/")
        self.assertEqual(r.status_code, 200)
        link = r.json()["link_convite"]
        self.assertTrue(link["url"].startswith("https://front.test/convite/"))
        # só o criador vê o link
        ParticipanteEquipe.objects.create(user=self.u2, equipe=self.equipe)
        self.assertIsNone(self.as_user(self.u2).get("/api/me/equipes/").json()[0]["link_convite"])
        self.assertEqual(self.as_user(self.u3).post(f"/api/convites/{link['token']}/aceitar/").status_code, 200)
        # lotou (3): quarto não entra
        self.assertEqual(self.as_user(self.u4).post(f"/api/convites/{link['token']}/aceitar/").status_code, 400)

    def test_revogar_e_cancelar(self):
        c = self.as_user(self.u1)
        token = c.post(self.url + "link-convite/").json()["link_convite"]["token"]
        c.delete(self.url + "link-convite/")
        self.assertEqual(self.as_user(self.u3).post(f"/api/convites/{token}/aceitar/").status_code, 400)
        c = self.as_user(self.u1)
        r = c.post(self.url + "membros/", {"membros": ["novo@t.com"]}, format="json").json()
        cid = r["convites"][0]["id"]
        self.assertEqual(c.delete(f"{self.url}convites/{cid}/").json()["convites"], [])
        ParticipanteEquipe.objects.create(user=self.u2, equipe=self.equipe)
        self.assertEqual(self.as_user(self.u2).delete(f"{self.url}convites/{cid}/").status_code, 403)

    def test_nao_aceita_fora_das_inscricoes_nem_nao_participante(self):
        token = self.as_user(self.u1).post(self.url + "link-convite/").json()["link_convite"]["token"]
        self.assertEqual(self.as_user(self.aval).post(f"/api/convites/{token}/aceitar/").status_code, 403)
        self.edicao.status = "EM_ANDAMENTO"
        self.edicao.save()
        self.assertEqual(self.as_user(self.u3).post(f"/api/convites/{token}/aceitar/").status_code, 400)
        self.assertFalse(self.client.get(f"/api/convites/{token}/").json()["valido"])

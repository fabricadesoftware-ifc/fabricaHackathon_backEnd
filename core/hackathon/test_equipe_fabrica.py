from .models import AvaliadorEdicao, Criterio, Equipe, Nota
from .test_regras_negocio import Base


class EquipeFabricaTest(Base):
    def setUp(self):
        super().setUp()
        self.base = f"/api/painel/edicoes/{self.edicao.id}/"
        self.crit = Criterio.objects.create(nome="Inovação", edicao=self.edicao)
        self.vinculo = AvaliadorEdicao.objects.create(avaliador=self.aval, edicao=self.edicao)

    def criar(self, **extra):
        corpo = {"nome_equipe": "Fábrica", "nome_projeto": "Sistema da Fábrica", "membros": ["u1@t.com"]}
        corpo.update(extra)
        return self.as_user(self.admin).post(self.base + "equipe-fabrica/", corpo, format="json")

    def test_admin_cadastra_e_so_admin(self):
        r = self.criar()
        self.assertEqual(r.status_code, 201, r.content)
        equipe = Equipe.objects.get(nome_equipe="Fábrica")
        self.assertTrue(equipe.organizadora)
        self.assertEqual(equipe.participantes.count(), 1)
        self.assertEqual(self.as_user(self.prof).post(self.base + "equipe-fabrica/", {}, format="json").status_code, 403)
        # nome repetido, e-mail inexistente e sem nome
        self.assertEqual(self.criar().status_code, 400)
        self.assertEqual(self.criar(nome_equipe="Outra", membros=["nao@t.com"]).status_code, 400)
        self.assertEqual(self.as_user(self.admin).post(self.base + "equipe-fabrica/", {}, format="json").status_code, 400)

    def test_nao_conta_no_limite_de_equipes(self):
        self.edicao.maximo_equipes = 1
        self.edicao.save()
        self.criar(membros=[])
        self.assertEqual(self.inscrever().status_code, 201)  # a da Fábrica não ocupou a vaga
        r = self.client.get("/api/edicoes/")
        self.assertEqual(r.status_code, 200)

    def test_fora_da_avaliacao(self):
        self.criar(membros=[])
        equipe = Equipe.objects.get(nome_equipe="Fábrica")
        normal = self.criar_equipe("Normal", self.u2)
        self.edicao.status = "AVALIACAO"
        self.edicao.save()
        c = self.as_user(self.aval)
        # não aparece para o avaliador e não aceita nota
        nomes = [i["projeto"]["equipe"] for i in c.get("/api/me/avaliacoes/").json()]
        self.assertEqual(nomes, ["Normal"])
        corpo = {"nota": "8.00", "projeto": equipe.projeto_id, "criterio": self.crit.id}
        self.assertEqual(c.post("/api/notas/", corpo, format="json").status_code, 400)
        lote = {"projeto": equipe.projeto_id, "notas": [{"criterio": self.crit.id, "nota": "8.00"}]}
        self.assertEqual(c.post("/api/notas/lote/", lote, format="json").status_code, 400)
        # a equipe normal é avaliada; a da Fábrica fica sem nota final e fora do ranking e dos resultados
        Nota.objects.create(nota="9.00", projeto=normal.projeto, criterio=self.crit, avaliador=self.vinculo)
        from .services.nota_final import recalcular_nota_final
        recalcular_nota_final(normal.projeto)
        recalcular_nota_final(equipe.projeto)
        equipe.projeto.refresh_from_db()
        self.assertIsNone(equipe.projeto.notaFinal_projeto)
        self.edicao.status = "FINALIZADO"
        self.edicao.save()
        ranking = self.client.get(f"/api/edicoes/{self.edicao.id}/ranking/").json()
        self.assertEqual([i["equipe"] for i in ranking], ["Normal"])
        res = self.as_user(self.admin).get(self.base + "resultados/").json()["resultados"]
        self.assertEqual([r["equipe"] for r in res], ["Normal"])

    def test_marcacao_publica_e_toggle(self):
        self.criar(membros=[])
        self.client.force_authenticate(user=None)
        detalhe = self.client.get(f"/api/edicoes/{self.edicao.id}/").json()
        marcas = {e["nome_equipe"]: e["organizadora"] for e in detalhe["equipes"]}
        self.assertEqual(marcas, {"Fábrica": True})
        equipe = Equipe.objects.get(nome_equipe="Fábrica")
        c = self.as_user(self.admin)
        r = c.patch(f"{self.base}equipes/{equipe.id}/", {"organizadora": False}, format="json")
        self.assertFalse(r.json()["organizadora"])
        r = c.patch(f"{self.base}equipes/{equipe.id}/", {"organizadora": True}, format="json")
        self.assertTrue(r.json()["organizadora"])
        self.assertEqual(self.as_user(self.u1).patch(f"{self.base}equipes/{equipe.id}/", {"organizadora": False}, format="json").status_code, 403)

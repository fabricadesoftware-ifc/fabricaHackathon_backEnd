from datetime import timedelta
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone

from .models import AvaliadorEdicao, Criterio, Nota, PreAvaliacao
from .services.nota_final import recalcular_nota_final
from .services.pre_avaliacao import link_local, pontuar
from .test_regras_negocio import Base

STORAGES_TESTE = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "documentos": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
TEXTO = "x" * 40


class LinkLocalTest(Base):
    def test_detecta_links_locais(self):
        locais = [
            "http://localhost:3000", "http://127.0.0.1:8000/app", "http://192.168.0.10",
            "http://10.0.0.5/x", "http://172.16.4.2", "http://meuservidor/app", "http://app.local",
            "http://[::1]:8000",
        ]
        for url in locais:
            self.assertTrue(link_local(url), url)
        for url in ["https://app.fabricadesoftware.ifc.edu.br", "https://meuapp.vercel.app", "http://8.8.8.8"]:
            self.assertFalse(link_local(url), url)
        self.assertFalse(link_local(""))


@override_settings(STORAGES=STORAGES_TESTE)
class PreAvaliacaoTest(Base):
    def setUp(self):
        super().setUp()
        self.edicao.status = "EM_ANDAMENTO"
        self.edicao.pre_avaliacao_liberada = True
        self.edicao.save()
        self.equipe = self.criar_equipe("Alfa", self.u1, (self.u2,))
        self.projeto = self.equipe.projeto
        self.url = f"/api/me/projetos/{self.projeto.id}/pre-avaliacao/"

    def completo(self, **kw):
        corpo = {
            "responsabilidades": [{"user": self.u1.id, "area": "back"}, {"user": self.u2.id, "area": "front"}],
            "organizacao_metodo": "KANBAN",
            "problema_entendido": TEXTO, "problema_explicacao": TEXTO,
            "maior_dificuldade": TEXTO, "proximos_passos": TEXTO,
            "arquitetura_link": "https://drive.example.com/arq",
            "hospedagem_plataforma": "FABROKU", "hospedagem_link": "https://app.example.com",
            "hospedagem_justificativa": TEXTO,
            "banco_plataforma": "FABROKU_POSTGRES", "banco_justificativa": TEXTO,
        }
        corpo.update(kw)
        return corpo

    def rfs(self, nome="rfs.pdf"):
        return SimpleUploadedFile(nome, b"%PDF-1.4 conteudo", content_type="application/pdf")

    def enviar(self, user=None, corpo=None, arquivos=True):
        corpo = self.completo() if corpo is None else corpo
        c = self.as_user(user or self.u1)
        if arquivos:
            dados = {k: v for k, v in corpo.items() if k != "responsabilidades"}
            dados["arquivo_rfs_rnfs"] = self.rfs()
            if "responsabilidades" in corpo:
                import json
                dados["responsabilidades"] = json.dumps(corpo["responsabilidades"])
            return c.patch(self.url, dados, format="multipart")
        return c.patch(self.url, corpo, format="json")

    def test_link_de_hospedagem_vira_link_publico_do_projeto(self):
        r = self.enviar()
        self.assertEqual(r.status_code, 200, r.content)
        self.projeto.refresh_from_db()
        self.assertEqual(self.projeto.link_deploy_projeto, "https://app.example.com")

    def test_link_local_nao_e_publicado(self):
        r = self.enviar(corpo=self.completo(hospedagem_link="http://localhost:3000"))
        self.assertEqual(r.status_code, 200, r.content)
        self.projeto.refresh_from_db()
        self.assertFalse(self.projeto.link_deploy_projeto)

    # --- pontuação -----------------------------------------------------
    def test_formulario_completo_vale_10(self):
        r = self.enviar()
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()["nota"], "10.00")  # RFs por arquivo, arquitetura por link, nada local

    def test_sem_peso_interno_respondeu_10_nao_respondeu_0(self):
        membros = [self.u1.id, self.u2.id]
        total, _ = pontuar(PreAvaliacao(projeto=self.projeto), membros)
        self.assertEqual(total, Decimal("0.00"))
        # qualquer resposta registrada vale 10: não há nota parcial por item/seção
        total, _ = pontuar(PreAvaliacao(projeto=self.projeto, problema_entendido="curto"), membros)
        self.assertEqual(total, Decimal("10.00"))
        # mesmo tudo local e sem arquivos: vale 10
        pre = PreAvaliacao(projeto=self.projeto, hospedagem_plataforma="LOCAL", banco_plataforma="LOCAL")
        self.assertEqual(pontuar(pre, membros)[0], Decimal("10.00"))

    def test_formulario_parcial_via_api_vale_10(self):
        r = self.as_user(self.u1).patch(self.url, {"organizacao_metodo": "KANBAN"}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()["nota"], "10.00")

    def test_so_membros_escrevem(self):
        for user in (self.u3, self.prof, self.admin, self.aval):
            self.assertEqual(self.as_user(user).patch(self.url, {}, format="json").status_code, 403)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.patch(self.url, {}, format="json").status_code, 401)

    def test_leitura_permitida_a_membro_admin_professor_e_avaliador_da_edicao(self):
        AvaliadorEdicao.objects.create(avaliador=self.aval, edicao=self.edicao)
        for user in (self.u1, self.u2, self.admin, self.prof, self.aval):
            self.assertEqual(self.as_user(user).get(self.url).status_code, 200, user)
        for user in (self.u3, self.aval2):
            self.assertEqual(self.as_user(user).get(self.url).status_code, 403, user)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_get_sem_preenchimento_devolve_formulario_vazio(self):
        corpo = self.as_user(self.u1).get(self.url).json()
        self.assertFalse(corpo["preenchida"])
        self.assertTrue(corpo["aberta"])
        self.assertEqual(corpo["nota"], "0.00")
        self.assertEqual({i["id"] for i in corpo["integrantes"]}, {self.u1.id, self.u2.id})
        self.assertIn("KANBAN", [o["valor"] for o in corpo["opcoes"]["organizacao_metodo"]])

    def test_fechada_quando_nao_liberada_fora_do_prazo_ou_fora_de_andamento(self):
        self.edicao.pre_avaliacao_liberada = False
        self.edicao.save()
        r = self.enviar(arquivos=False)
        self.assertEqual(r.status_code, 403)
        self.assertIn("não foi liberada", str(r.json()))
        self.edicao.pre_avaliacao_liberada = True
        self.edicao.prazo_pre_avaliacao = timezone.now() - timedelta(minutes=1)
        self.edicao.save()
        r = self.enviar(arquivos=False)
        self.assertEqual(r.status_code, 403)
        self.assertIn("prazo", str(r.json()))
        self.assertFalse(self.as_user(self.u1).get(self.url).json()["aberta"])
        self.edicao.prazo_pre_avaliacao = timezone.now() + timedelta(hours=1)
        self.edicao.save()
        self.assertEqual(self.enviar(arquivos=False).status_code, 200)
        for status in ("AVALIACAO", "FINALIZADO"):
            self.edicao.status = status
            self.edicao.save()
            self.assertEqual(self.enviar(arquivos=False).status_code, 403, status)

    def test_resposta_antes_do_fechamento_fica_gravada_e_depois_nao_muda(self):
        self.assertEqual(self.enviar(arquivos=False).status_code, 200)
        nota = PreAvaliacao.objects.get(projeto=self.projeto).nota
        self.edicao.status = "AVALIACAO"
        self.edicao.save()
        self.enviar(arquivos=False, corpo={"problema_entendido": ""})
        self.assertEqual(PreAvaliacao.objects.get(projeto=self.projeto).nota, nota)

    # --- validações ---------------------------------------------------
    def test_validacoes_de_link_responsaveis_e_arquivo(self):
        for corpo in (
            {"hospedagem_link": "ftp://x.com/arquivo"},
            {"hospedagem_link": "isso nao e url"},
            {"responsabilidades": [{"user": self.u3.id, "area": "back"}]},
            {"responsabilidades": [{"user": self.u1.id, "area": "a"}, {"user": self.u1.id, "area": "b"}]},
            {"responsabilidades": [{"user": self.u1.id, "area": ""}]},
            {"organizacao_metodo": "INVENTADO"},
        ):
            self.assertEqual(self.enviar(corpo=corpo, arquivos=False).status_code, 400, corpo)
        ruim = SimpleUploadedFile("virus.exe", b"MZ", content_type="application/octet-stream")
        r = self.as_user(self.u1).patch(self.url, {"arquivo_rfs_rnfs": ruim}, format="multipart")
        self.assertEqual(r.status_code, 400)
        self.assertIn("Formato", str(r.json()))

    def test_nota_e_pontuacao_nao_sao_editaveis(self):
        self.as_user(self.u1).patch(self.url, {"nota": "10.00"}, format="json")
        self.assertEqual(PreAvaliacao.objects.get(projeto=self.projeto).nota, Decimal("0.00"))

    # --- nota final ----------------------------------------------------
    def test_nota_final_90_avaliadores_mais_10_pre_avaliacao(self):
        self.edicao.status = "EM_ANDAMENTO"
        c = Criterio.objects.create(nome="C1", edicao=self.edicao)
        ae = AvaliadorEdicao.objects.create(avaliador=self.aval, edicao=self.edicao)
        self.enviar(corpo=self.completo(), arquivos=True)
        pre = PreAvaliacao.objects.get(projeto=self.projeto)
        self.assertEqual(pre.nota, Decimal("10.00"))
        Nota.objects.create(nota="8.00", projeto=self.projeto, criterio=c, avaliador=ae)
        self.projeto.refresh_from_db()
        self.assertEqual(self.projeto.notaFinal_projeto, Decimal("8.20"))  # 8*0,9 + 10*0,1
        pre.delete()
        recalcular_nota_final(self.projeto)
        self.projeto.refresh_from_db()
        self.assertEqual(self.projeto.notaFinal_projeto, Decimal("7.20"))  # sem pré-avaliação conta 0

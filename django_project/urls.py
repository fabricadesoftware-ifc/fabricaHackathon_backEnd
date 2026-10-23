from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include

from rest_framework.routers import DefaultRouter

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core.hackathon.views import (
    ApoiadorViewSet,
    TipoEdicaoViewSet,
    UserViewSet,
    EdicaoViewSet,
    CriterioViewSet,
    TemaViewSet,
    ProjetoViewSet,
    EquipeViewSet,
    NotaViewSet,
    ParticipanteEquipeViewSet,
    AvaliadorEdicaoViewSet,
    CustomTokenObtainPairView,
)
from core.hackathon.views.registro import RegistroView, SolicitacaoPerfilViewSet
from core.hackathon.views.convite import ConviteAceitarView, ConviteInfoView
from core.hackathon.views.inscricao import InscricaoViewSet
from core.hackathon.views.painel import (
    PainelAvaliadoresView,
    PainelEdicaoView,
    PainelEdicoesView,
    PainelEquipesView,
    PainelResultadosView,
)
from core.hackathon.views.preAvaliacao import PreAvaliacaoView
from core.hackathon.views.me import (
    MeView,
    MinhasAvaliacoesView,
    MinhasEquipesView,
    MeusProjetosView,
)



def health(request):
    return JsonResponse({"status": "ok"})


router = DefaultRouter()
router.register(r"apoiadores", ApoiadorViewSet)
router.register(r"tipos-edicao", TipoEdicaoViewSet)
router.register(r"users", UserViewSet)
router.register(r"edicoes", EdicaoViewSet)
router.register(r"criterios", CriterioViewSet)
router.register(r"temas", TemaViewSet)
router.register(r"projetos", ProjetoViewSet)
router.register(r"equipes", EquipeViewSet)
router.register(r"notas", NotaViewSet)
router.register(r"participantes-equipe", ParticipanteEquipeViewSet)
router.register(r"avaliadores", AvaliadorEdicaoViewSet)
router.register(r"solicitacoes-perfil", SolicitacaoPerfilViewSet, basename="solicitacao-perfil")
router.register(r"inscricoes", InscricaoViewSet, basename="inscricao")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/auth/registro/", RegistroView.as_view(), name="registro"),
    path("api/painel/edicoes/", PainelEdicoesView.as_view(), name="painel-edicoes"),
    path("api/painel/edicoes/<int:pk>/", PainelEdicaoView.as_view(), name="painel-edicao"),
    path("api/painel/edicoes/<int:pk>/equipes/", PainelEquipesView.as_view(), name="painel-equipes"),
    path("api/painel/edicoes/<int:pk>/resultados/", PainelResultadosView.as_view(), name="painel-resultados"),
    path("api/painel/edicoes/<int:pk>/avaliadores/", PainelAvaliadoresView.as_view(), name="painel-avaliadores"),
    path("api/painel/edicoes/<int:pk>/avaliadores/<int:user_id>/", PainelAvaliadoresView.as_view(), name="painel-avaliador"),
    path("api/convites/<str:token>/", ConviteInfoView.as_view(), name="convite-info"),
    path("api/convites/<str:token>/aceitar/", ConviteAceitarView.as_view(), name="convite-aceitar"),
    path("api/me/", MeView.as_view(), name="me"),
    path("api/me/equipes/", MinhasEquipesView.as_view(), name="me-equipes"),
    path("api/me/projetos/", MeusProjetosView.as_view(), name="me-projetos"),
    path("api/me/projetos/<int:projeto_id>/pre-avaliacao/", PreAvaliacaoView.as_view(), name="me-pre-avaliacao"),
    path("api/me/avaliacoes/", MinhasAvaliacoesView.as_view(), name="me-avaliacoes"),
    path("api/", include(router.urls)),
    path("api/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

from django.contrib import admin
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

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

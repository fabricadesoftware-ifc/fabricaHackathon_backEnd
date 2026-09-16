from django.contrib import admin
from django.urls import path, include

from rest_framework.routers import DefaultRouter
from core.hackathon.views import (
    ApoiadorViewSet,
    TipoEdicaoViewSet,
    TipoUserViewSet,
    UserViewSet,
    EdicaoViewSet,
    CriterioViewSet,
    TemaViewSet,
    ProjetoViewSet,
    EquipeViewSet,
    NotaViewSet,
)

router = DefaultRouter()
router.register(r'apoiadores', ApoiadorViewSet)
router.register(r'tipos-edicao', TipoEdicaoViewSet)
router.register(r'tipos-user', TipoUserViewSet)
router.register(r'users', UserViewSet)
router.register(r'edicoes', EdicaoViewSet)
router.register(r'criterios', CriterioViewSet)
router.register(r'temas', TemaViewSet)
router.register(r'projetos', ProjetoViewSet)
router.register(r'equipes', EquipeViewSet)
router.register(r'notas', NotaViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]
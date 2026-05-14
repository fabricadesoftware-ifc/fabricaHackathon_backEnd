from django.contrib import admin
from django.urls import path, include

from rest_framework.routers import DefaultRouter
from core.hackathon.views import (
    ApoiadorViewSet,
    TipoEdicaoViewSet,
    TipoUserViewSet,
    EdicaoViewSet,
)

router = DefaultRouter()
router.register(r'apoiadores', ApoiadorViewSet)
router.register(r'tipos', TipoEdicaoViewSet)
router.register(r'tipos-user', TipoUserViewSet)
router.register(r'edicoes', EdicaoViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
]
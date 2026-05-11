from django.contrib import admin
from django.urls import path, include

from core.hackathon.views import ApoiadorViewSet, TipoEdicaoViewSet

from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'apoiadores', ApoiadorViewSet)
router.register(r"tipos", TipoEdicaoViewSet)



urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include(router.urls))
]

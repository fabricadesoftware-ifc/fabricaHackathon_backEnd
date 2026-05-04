from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet

from ..models import Apoiador
from ..serializers import ApoiadorSerializer, ApoiadorListSerializer

class ApoiadorViewSet(ModelViewSet):
    queryset = Apoiador.objects.all()
    def get_serializer_class(self):
        if self.action == "create":
            return ApoiadorSerializer
        elif self.action in ("list", "retrive"):
            return ApoiadorListSerializer
        else:
            return ApoiadorListSerializer
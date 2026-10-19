from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet

from ..models import Apoiador
from ..permissions import IsAdminOrReadOnly
from ..serializers import ApoiadorSerializer, ApoiadorListSerializer

class ApoiadorViewSet(ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = Apoiador.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return ApoiadorSerializer

        elif self.action == "list":
            return ApoiadorListSerializer

        else:
            return ApoiadorSerializer
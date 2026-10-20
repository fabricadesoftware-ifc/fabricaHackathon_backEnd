from rest_framework.viewsets import ModelViewSet
from ..models import ParticipanteEquipe
from ..permissions import IsAdminOrReadOnly, is_admin, is_professor
from ..serializers import ParticipanteEquipeSerializer, ParticipanteEquipeListSerializer
from .mixins import BloqueiaEdicaoFinalizadaMixin

class ParticipanteEquipeViewSet(BloqueiaEdicaoFinalizadaMixin, ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = ParticipanteEquipe.objects.all().order_by('id')
    serializer_class = ParticipanteEquipeSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if is_admin(user) or is_professor(user):
            return queryset
        # Demais perfis só enxergam os integrantes das próprias equipes.
        return queryset.filter(equipe__participantes__user=user)

    def edicao_da_instancia(self, instance):
        return instance.equipe.edicao

    def edicao_dos_dados(self, validated_data):
        equipe = validated_data.get('equipe')
        return equipe.edicao if equipe else None

    def get_serializer_class(self):
        if self.action == 'list':
            return ParticipanteEquipeListSerializer
        return super().get_serializer_class()

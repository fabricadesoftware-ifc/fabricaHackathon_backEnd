from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from ..models import Nota
from ..permissions import IsAvaliadorDaEdicaoOrReadOnly, is_admin, is_avaliador, is_professor
from ..serializers import (
    NotaSerializer,
    NotaListSerializer,
    NotaLoteSerializer,
)
from .mixins import BloqueiaEdicaoFinalizadaMixin, bloquear_se_finalizada

class NotaViewSet(BloqueiaEdicaoFinalizadaMixin, ModelViewSet):
    permission_classes = [IsAvaliadorDaEdicaoOrReadOnly]
    queryset = Nota.objects.all().order_by('id')
    serializer_class = NotaSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if is_admin(user) or is_professor(user):
            return queryset
        if is_avaliador(user):
            # O avaliador só enxerga as próprias notas.
            return queryset.filter(avaliador__avaliador=user)
        return queryset.none()

    def edicao_da_instancia(self, instance):
        return instance.projeto.edicao

    def edicao_dos_dados(self, validated_data):
        projeto = validated_data.get('projeto')
        return projeto.edicao if projeto else None

    def perform_destroy(self, instance):
        bloquear_se_finalizada(instance.projeto.edicao)
        if instance.projeto.edicao.status != 'AVALIACAO':
            raise ValidationError({'detail': 'Notas só podem ser removidas durante a fase de avaliação.'})
        super().perform_destroy(instance)

    def get_serializer_class(self):
        if self.action == 'list':
            return NotaListSerializer
        elif self.action == 'lote':
            return NotaLoteSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['post'], url_path='lote')
    def lote(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        bloquear_se_finalizada(serializer.validated_data['projeto'].edicao)
        notas_criadas = serializer.save()
        return Response(
            NotaSerializer(notas_criadas, many=True).data,
            status=status.HTTP_201_CREATED
        )

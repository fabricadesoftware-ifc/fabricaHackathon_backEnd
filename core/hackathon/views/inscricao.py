from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from ..models import Equipe
from ..permissions import IsParticipante
from ..serializers.inscricao import (
    InscricaoAtualizacaoSerializer,
    InscricaoSerializer,
    MembrosSerializer,
    MinhaEquipeSerializer,
)
from ..services import inscricao as servico


class InscricaoViewSet(GenericViewSet):
    """
    Inscrição de equipes (somente PARTICIPANTE). Escritas valem apenas enquanto a
    edição está em INSCRICAO; alterações de equipe são do criador.
    """

    permission_classes = [IsParticipante]
    serializer_class = InscricaoSerializer

    def get_queryset(self):
        return (
            Equipe.objects.filter(participantes__user=self.request.user)
            .select_related('tema', 'edicao', 'projeto__edicao', 'criador')
            .prefetch_related('participantes__user')
        )

    def _equipe_do_criador(self):
        equipe = self.get_object()
        if equipe.criador_id != self.request.user.pk:
            raise PermissionDenied('Apenas o criador da equipe pode fazer esta alteração.')
        return equipe

    def _resposta(self, equipe, codigo=status.HTTP_200_OK):
        equipe = self.get_queryset().get(pk=equipe.pk)
        dados = MinhaEquipeSerializer(equipe, context={'request': self.request}).data
        return Response(dados, status=codigo)

    def create(self, request):
        serializer = InscricaoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        equipe = servico.criar_inscricao(request.user, serializer.validated_data)
        return self._resposta(equipe, status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        equipe = self._equipe_do_criador()
        serializer = InscricaoAtualizacaoSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        servico.atualizar_equipe(equipe, serializer.validated_data)
        return self._resposta(equipe)

    def destroy(self, request, pk=None):
        equipe = self._equipe_do_criador()
        servico.excluir_equipe(equipe)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='membros')
    def adicionar_membros(self, request, pk=None):
        equipe = self._equipe_do_criador()
        serializer = MembrosSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        servico.adicionar_membros(equipe, serializer.validated_data['membros'])
        return self._resposta(equipe)

    @action(detail=True, methods=['delete'], url_path=r'membros/(?P<usuario_id>\d+)')
    def remover_membro(self, request, pk=None, usuario_id=None):
        equipe = self._equipe_do_criador()
        servico.remover_membro(equipe, int(usuario_id))
        return self._resposta(equipe)

    @action(detail=True, methods=['post'], url_path='sair')
    def sair(self, request, pk=None):
        equipe = self.get_object()
        if equipe.criador_id == request.user.pk:
            raise PermissionDenied('O criador não pode sair da equipe; exclua a equipe se necessário.')
        servico.remover_membro(equipe, request.user.pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

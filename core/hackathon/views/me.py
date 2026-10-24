from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import AvaliadorEdicao, Criterio, Equipe, Nota, Projeto
from ..permissions import is_admin, is_avaliador, is_participante, is_professor
from ..serializers.inscricao import MeSerializer, MeuProjetoSerializer, MinhaEquipeSerializer, PerfilSerializer


class MeView(APIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        return Response(MeSerializer(request.user, context={'request': request}).data)

    def patch(self, request):
        """Atualiza só nome, sobrenome e foto do próprio usuário (JSON ou multipart)."""
        serializer = PerfilSerializer(request.user, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(MeSerializer(request.user, context={'request': request}).data)


def _ve_tudo(user):
    # Professor e administrador leem todas as equipes/projetos (somente leitura).
    return is_professor(user) or is_admin(user)


class MinhasEquipesView(ListAPIView):
    """Participante: só as próprias equipes. Professor/administrador: todas."""

    serializer_class = MinhaEquipeSerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        queryset = (
            Equipe.objects.select_related('tema', 'edicao', 'projeto__edicao', 'criador')
            .prefetch_related('participantes__user')
            .order_by('edicao_id', 'nome_equipe', 'id')
        )
        if _ve_tudo(user):
            return queryset
        if is_participante(user):
            return queryset.filter(participantes__user=user)
        raise PermissionDenied('Este perfil não possui equipes.')


class MeusProjetosView(ListAPIView):
    serializer_class = MeuProjetoSerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        queryset = Projeto.objects.select_related('edicao', 'equipes').order_by('edicao_id', 'nome_projeto', 'id')
        if _ve_tudo(user):
            return queryset
        if is_participante(user):
            return queryset.filter(equipes__participantes__user=user)
        raise PermissionDenied('Este perfil não possui projetos.')


class MinhasAvaliacoesView(APIView):
    """Avaliador: projetos das edições em que está vinculado, com avaliados/pendentes."""

    def get(self, request):
        if not is_avaliador(request.user):
            raise PermissionDenied('Apenas avaliadores acessam as próprias avaliações.')

        vinculos = list(AvaliadorEdicao.objects.filter(avaliador=request.user).select_related('edicao'))
        itens = []
        for vinculo in vinculos:
            edicao = vinculo.edicao
            criterios = list(Criterio.objects.filter(edicao=edicao).order_by('id'))
            notas = {}
            for nota in Nota.objects.filter(avaliador=vinculo):
                notas.setdefault(nota.projeto_id, {})[nota.criterio_id] = nota
            projetos = Projeto.objects.filter(edicao=edicao).exclude(equipes__organizadora=True).select_related('equipes').order_by('nome_projeto', 'id')
            for projeto in projetos:
                feitas = notas.get(projeto.id, {})
                pendentes = [c for c in criterios if c.id not in feitas]
                equipe = getattr(projeto, 'equipes', None)
                itens.append({
                    'edicao': edicao.id,
                    'edicao_nome': edicao.nome,
                    'edicao_status': edicao.status,
                    'avaliacao_aberta': edicao.status == 'AVALIACAO',
                    'avaliador_id': vinculo.id,
                    'projeto': {
                        'id': projeto.id,
                        'nome_projeto': projeto.nome_projeto,
                        'descricao_projeto': projeto.descricao_projeto,
                        'link_deploy_projeto': projeto.link_deploy_projeto,
                        'equipe': equipe.nome_equipe if equipe else None,
                    },
                    'total_criterios': len(criterios),
                    'criterios_avaliados': [
                        {'criterio_id': c.id, 'criterio': c.nome, 'nota_id': feitas[c.id].id, 'nota': feitas[c.id].nota}
                        for c in criterios if c.id in feitas
                    ],
                    'criterios_pendentes': [{'criterio_id': c.id, 'criterio': c.nome} for c in pendentes],
                    'concluido': bool(criterios) and not pendentes,
                })
        return Response(itens)

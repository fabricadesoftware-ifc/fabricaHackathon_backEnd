from django.db.models import Count
from django.db.models import Prefetch
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from ..models import Edicao, Equipe, Projeto
from ..permissions import ReadOnlyOrAuthenticated
from ..query_params import int_param
from .mixins import BloqueiaEdicaoFinalizadaMixin
from ..serializers import EdicaoSerializer
from ..serializers import EdicaoListSerializer
from ..serializers.public import EdicaoDetailPublicSerializer, RankingSerializer


class EdicaoViewSet(BloqueiaEdicaoFinalizadaMixin, ModelViewSet):
    permission_classes = [ReadOnlyOrAuthenticated]
    queryset = Edicao.objects.all()
    serializer_class = EdicaoSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["nome"]
    ordering_fields = ["data_inicio", "nome", "ano"]
    ordering = ["-data_inicio", "-id"]

    def edicao_da_instancia(self, instance):
        return instance

    def edicao_dos_dados(self, validated_data):
        return None

    def get_serializer_class(self):
        if self.action == 'list':
            return EdicaoListSerializer
        if self.action in ('retrieve', 'ranking'):
            return EdicaoDetailPublicSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action not in ('list', 'retrieve', 'ranking'):
            return queryset

        queryset = queryset.select_related('tipo_edicao').annotate(total_equipes=Count('equipes'))

        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                'apoiadores',
                'criterios',
                'temas',
                Prefetch(
                    'equipes',
                    queryset=Equipe.objects.select_related('tema', 'projeto__edicao').order_by('nome_equipe'),
                ),
            )

        if self.action == 'list':
            params = self.request.query_params
            status = params.get('status')
            if status:
                if status not in dict(Edicao.STATUS_CHOICES):
                    raise ValidationError(
                        {'status': f"Valor inválido. Use um de: {', '.join(dict(Edicao.STATUS_CHOICES))}."}
                    )
                queryset = queryset.filter(status=status)
            ano = int_param(self.request, 'ano')
            if ano is not None:
                queryset = queryset.filter(ano=ano)
            tipo_edicao = int_param(self.request, 'tipo_edicao')
            if tipo_edicao is not None:
                queryset = queryset.filter(tipo_edicao_id=tipo_edicao)
        return queryset

    @action(detail=True, methods=['get'], pagination_class=None)
    def ranking(self, request, pk=None):
        edicao = self.get_object()
        if edicao.status != 'FINALIZADO':
            raise PermissionDenied('O ranking só fica disponível quando a edição está finalizada.')

        projetos = (
            Projeto.objects.filter(edicao=edicao, notaFinal_projeto__isnull=False)
            .select_related('equipes')
            .order_by('-notaFinal_projeto', 'nome_projeto', 'id')
        )
        itens = []
        anterior = None
        posicao = 0
        for indice, projeto in enumerate(projetos, start=1):
            # Empates dividem a posição (1, 2, 2, 4).
            if projeto.notaFinal_projeto != anterior:
                posicao = indice
                anterior = projeto.notaFinal_projeto
            equipe = getattr(projeto, 'equipes', None)
            itens.append({
                'posicao': posicao,
                'projeto_id': projeto.id,
                'projeto': projeto.nome_projeto,
                'equipe': equipe.nome_equipe if equipe else None,
                'nota_final': projeto.notaFinal_projeto,
            })
        return Response(RankingSerializer(itens, many=True).data)

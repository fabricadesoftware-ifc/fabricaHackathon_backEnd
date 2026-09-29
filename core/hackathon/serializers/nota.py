from decimal import Decimal
from django.db import transaction
from rest_framework import serializers
from ..models import Nota, AvaliadorEdicao, Projeto, Criterio
from ..validations.nota_validation import validate_nota_edicao, validate_nota_unica


class NotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nota
        fields = [
            "id",
            "nota",
            "comentario_nota",
            "projeto",
            "criterio",
            "avaliador",
        ]

    def validate(self, attrs):
        avaliador = attrs.get('avaliador', getattr(self.instance, 'avaliador', None))
        projeto = attrs.get('projeto', getattr(self.instance, 'projeto', None))
        criterio = attrs.get('criterio', getattr(self.instance, 'criterio', None))

        validate_nota_edicao(avaliador, projeto, criterio)
        validate_nota_unica(avaliador, projeto, criterio, instance=self.instance)
        return attrs


class NotaListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nota
        fields = [
            "id",
            "nota",
            "projeto",
            "criterio",
            "avaliador",
        ]


class ItemNotaLoteSerializer(serializers.Serializer):
    criterio = serializers.PrimaryKeyRelatedField(queryset=Criterio.objects.all())
    nota = serializers.DecimalField(
        max_digits=4,
        decimal_places=2,
        min_value=Decimal('0.00'),
        max_value=Decimal('10.00')
    )
    comentario_nota = serializers.CharField(required=False, allow_blank=True, allow_null=True, default='')


class NotaLoteSerializer(serializers.Serializer):
    avaliador = serializers.PrimaryKeyRelatedField(queryset=AvaliadorEdicao.objects.all())
    projeto = serializers.PrimaryKeyRelatedField(queryset=Projeto.objects.all())
    notas = ItemNotaLoteSerializer(many=True)

    def validate(self, attrs):
        avaliador = attrs.get('avaliador')
        projeto = attrs.get('projeto')
        notas_data = attrs.get('notas', [])

        if not notas_data:
            raise serializers.ValidationError({"notas": "A lista de notas não pode ser vazia."})

        # 1. Validação de edição entre avaliador e projeto
        if avaliador.edicao_id != projeto.edicao_id:
            raise serializers.ValidationError({
                "avaliador": "O avaliador não pertence à mesma edição do projeto avaliado."
            })

        criterios_ids = []
        for item in notas_data:
            criterio = item['criterio']
            # 2. Critério deve pertencer à mesma edição do projeto
            if criterio.edicao_id != projeto.edicao_id:
                raise serializers.ValidationError({
                    "notas": f"O critério '{criterio.nome}' não pertence à edição do projeto avaliado."
                })
            criterios_ids.append(criterio.id)

        # 3. Não permitir critérios duplicados no mesmo lote
        if len(criterios_ids) != len(set(criterios_ids)):
            raise serializers.ValidationError({
                "notas": "Existem critérios duplicados no lote de notas enviado."
            })

        # 4. Verificar se o avaliador já avaliou algum desses critérios para o projeto
        notas_existentes = Nota.objects.filter(
            avaliador=avaliador,
            projeto=projeto,
            criterio_id__in=criterios_ids
        ).values_list('criterio__nome', flat=True)

        if notas_existentes:
            nomes = ", ".join(notas_existentes)
            raise serializers.ValidationError({
                "notas": f"O avaliador já avaliou o(s) critério(s) '{nomes}' para este projeto."
            })

        return attrs

    def create(self, validated_data):
        avaliador = validated_data['avaliador']
        projeto = validated_data['projeto']
        notas_data = validated_data['notas']

        notas_criadas = []
        with transaction.atomic():
            for item in notas_data:
                nota_obj = Nota.objects.create(
                    avaliador=avaliador,
                    projeto=projeto,
                    criterio=item['criterio'],
                    nota=item['nota'],
                    comentario_nota=item.get('comentario_nota', '')
                )
                notas_criadas.append(nota_obj)

        return notas_criadas
from rest_framework.serializers import ModelSerializer, ValidationError

from ..models import Equipe

class EquipeSerializer(ModelSerializer):
    class Meta:
        model = Equipe
        fields = ['id', 'nome_equipe', 'edicao', 'tema', 'projeto', 'criador']

    def validate(self, attrs):
        edicao = attrs.get('edicao') or getattr(self.instance, 'edicao', None)
        tema = attrs.get('tema') or getattr(self.instance, 'tema', None)
        projeto = attrs.get('projeto') or getattr(self.instance, 'projeto', None)
        errors = {}
        if self.instance is None and edicao and edicao.equipes.count() >= edicao.maximo_equipes:
            errors['edicao'] = f"A edição já atingiu o limite de {edicao.maximo_equipes} equipes."
        if edicao and tema and tema.edicao_id != edicao.id:
            errors['tema'] = "O tema não pertence à edição informada."
        if edicao and projeto and projeto.edicao_id != edicao.id:
            errors['projeto'] = "O projeto não pertence à edição informada."
        if errors:
            raise ValidationError(errors)
        return attrs

class EquipeListSerializer(ModelSerializer):
    class Meta:
        model = Equipe
        fields = ['id', 'nome_equipe']

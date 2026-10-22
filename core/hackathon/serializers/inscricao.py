from rest_framework import serializers

from ..models import Edicao, Equipe, Projeto, Tema, User
from .imagem import LimpaImagensAntigasMixin
from .public import nota_final_publica


class ProjetoInscricaoSerializer(serializers.Serializer):
    nome_projeto = serializers.CharField(max_length=100)
    descricao_projeto = serializers.CharField(required=False, allow_blank=True)
    link_deploy_projeto = serializers.URLField(required=False, allow_null=True, allow_blank=True)


class InscricaoSerializer(serializers.Serializer):
    edicao = serializers.PrimaryKeyRelatedField(queryset=Edicao.objects.all())
    nome_equipe = serializers.CharField(max_length=50)
    tema = serializers.PrimaryKeyRelatedField(queryset=Tema.objects.all(), required=False, allow_null=True)
    projeto = ProjetoInscricaoSerializer()
    membros = serializers.ListField(
        child=serializers.EmailField(), required=False, default=list,
        help_text="E-mails dos demais membros (sem contar o criador).",
    )


class InscricaoAtualizacaoSerializer(serializers.Serializer):
    nome_equipe = serializers.CharField(max_length=50, required=False)
    tema = serializers.PrimaryKeyRelatedField(queryset=Tema.objects.all(), required=False)
    projeto = ProjetoInscricaoSerializer(partial=True, required=False)


class MembrosSerializer(serializers.Serializer):
    membros = serializers.ListField(child=serializers.EmailField(), allow_empty=False)


class MembroSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class MeuProjetoSerializer(serializers.ModelSerializer):
    nota_final = serializers.SerializerMethodField()
    equipe = serializers.SerializerMethodField()
    edicao_status = serializers.CharField(source='edicao.status', read_only=True)

    class Meta:
        model = Projeto
        fields = [
            'id', 'nome_projeto', 'descricao_projeto', 'link_deploy_projeto', 'logo_projeto',
            'edicao', 'edicao_status', 'equipe', 'nota_final',
        ]

    def get_nota_final(self, projeto):
        # A nota só aparece depois que a edição é marcada como FINALIZADO.
        return nota_final_publica(projeto)

    def get_equipe(self, projeto):
        equipe = getattr(projeto, 'equipes', None)
        return {'id': equipe.id, 'nome_equipe': equipe.nome_equipe} if equipe else None


class MinhaEquipeSerializer(serializers.ModelSerializer):
    tema = serializers.CharField(source='tema.descricao_tema', read_only=True, allow_null=True)
    tema_id = serializers.IntegerField(read_only=True)
    projeto = MeuProjetoSerializer(read_only=True)
    membros = serializers.SerializerMethodField()
    edicao_status = serializers.CharField(source='edicao.status', read_only=True)
    sou_criador = serializers.SerializerMethodField()

    class Meta:
        model = Equipe
        fields = [
            'id', 'nome_equipe', 'edicao', 'edicao_status', 'tema_id', 'tema',
            'criador', 'sou_criador', 'membros', 'projeto',
        ]

    def get_membros(self, equipe):
        return MembroSerializer([p.user for p in equipe.participantes.all()], many=True).data

    def get_sou_criador(self, equipe):
        request = self.context.get('request')
        return bool(request and equipe.criador_id == request.user.pk)


class MeSerializer(serializers.ModelSerializer):
    solicitacao_perfil = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'tipoUser', 'foto_perfil',
            'solicitacao_perfil',
        ]

    def get_solicitacao_perfil(self, user):
        ultima = user.solicitacoes_perfil.order_by('-criada_em', '-id').first()
        if ultima is None:
            return None
        return {'id': ultima.id, 'perfil_solicitado': ultima.perfil_solicitado, 'status': ultima.status}


class PerfilSerializer(LimpaImagensAntigasMixin, serializers.ModelSerializer):
    """Edição do próprio perfil: só nome, sobrenome e foto (usuário, e-mail e tipo não mudam aqui)."""

    campos_imagem = ('foto_perfil',)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'foto_perfil']
        extra_kwargs = {'foto_perfil': {'allow_null': True}}


class LogoProjetoSerializer(LimpaImagensAntigasMixin, serializers.ModelSerializer):
    """Troca/remoção da logo do projeto pelo criador da equipe (valida tamanho e formato)."""

    campos_imagem = ('logo_projeto',)

    class Meta:
        model = Projeto
        fields = ['logo_projeto']
        extra_kwargs = {'logo_projeto': {'allow_null': True}}

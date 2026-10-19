from rest_framework.serializers import ModelSerializer

from ..models import Apoiador
from .imagem import LimpaImagensAntigasMixin

class ApoiadorSerializer(LimpaImagensAntigasMixin, ModelSerializer):
    campos_imagem = ('logo_apoiador',)

    class Meta:
        model = Apoiador
        fields = ['id', 'nome', 'tipo', 'logo_apoiador']

class ApoiadorListSerializer(ModelSerializer):
    class Meta:
        model = Apoiador
        fields = ['id', 'nome', 'tipo', 'logo_apoiador']

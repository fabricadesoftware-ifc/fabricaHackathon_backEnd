from rest_framework.serializers import ModelSerializer

from ..models import Apoiador

class ApoiadorSerializer(ModelSerializer):
    class Meta: 
        model = Apoiador
        fields = ['nome', 'tipo']

class ApoiadorListSerializer(ModelSerializer):
    class Meta: 
        model = Apoiador
        fields = ['nome']
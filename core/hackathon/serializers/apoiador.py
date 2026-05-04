from rest_framework.serializers import ModelSerializer

from ..models import Apoiador

class ApoiadorSerializer(ModelSerializer):
    class Meta: 
        model = Apoiador
        fields = '__all__'

class ApoiadorListSerializer(ModelSerializer):
    class Meta: 
        model = Apoiador
        fields = ['nome']
from rest_framework.serializers import ModelSerializer
from ..models import TipoEdicao

class TipoEdicaoSerializer(ModelSerializer):
    class Meta:
        model = TipoEdicao
        fields = [
"id",
"nome"
]

from rest_framework.serializers import ModelSerializer
from ..models import Criterio

class CriterioSerializer(ModelSerializer):
    class Meta:
        model = Criterio
        fields = [
"id",
"nome",
"edicao",
]

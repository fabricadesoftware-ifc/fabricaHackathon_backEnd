from rest_framework.serializers import ModelSerializer
from ..models import Nota

class NotaSerializer(ModelSerializer):
    class Meta:
        model = Nota
        fields = [
            "id",
            "nota",
            "comentario_nota",
            "projeto",
            "criterio",
        ]
        
class NotaListSerializer(ModelSerializer):
    class Meta:
        model = Nota
        fields = [
            "id",
            "nota",
            "projeto",
        ]
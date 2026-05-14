from rest_framework import serializers
from ..models import Edicao
from ..validations.edicao_validation import validate_edicao
class EdicaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edicao
        fields = "__all__"
        
    def validate(self, data):
        return validate_edicao(data)

class EdicaoListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edicao
        fields = ["nome", "ano",]
            
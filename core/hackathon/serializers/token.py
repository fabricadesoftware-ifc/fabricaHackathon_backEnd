from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from ..models import User

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
            
        data['id'] = self.user.id
        data['username'] = self.user.username
        data['tipoUser'] = self.user.tipoUser
        return data
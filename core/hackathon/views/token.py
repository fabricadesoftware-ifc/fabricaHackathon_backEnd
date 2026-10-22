
from rest_framework_simplejwt.views import TokenObtainPairView

from ..serializers.token import CustomTokenObtainPairSerializer
from ..throttles import LoginRateThrottle

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]

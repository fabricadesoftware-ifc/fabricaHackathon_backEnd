from rest_framework.viewsets import ModelViewSet
from ..models import User
from ..serializers import UserSerializer, UserListSerializer

class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        return super().get_serializer_class()

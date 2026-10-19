from rest_framework.viewsets import ModelViewSet
from ..models import User
from ..permissions import IsAdmin, IsAdminOrSelf
from ..serializers import UserSerializer, UserListSerializer

class UserViewSet(ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer

    def get_permissions(self):
        # Listar, criar e apagar: somente administrador.
        # Ver/editar: administrador ou o próprio usuário.
        if self.action in ('list', 'create', 'destroy'):
            return [IsAdmin()]
        return [IsAdminOrSelf()]

    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        return super().get_serializer_class()

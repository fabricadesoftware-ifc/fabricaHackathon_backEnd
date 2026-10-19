from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import AvaliadorEdicao
from .models.user import tipoUser


def is_admin(user):
    return bool(
        user
        and user.is_authenticated
        and (user.is_superuser or getattr(user, "tipoUser", None) == tipoUser.admin)
    )


def is_avaliador(user):
    return bool(
        user
        and user.is_authenticated
        and getattr(user, "tipoUser", None) == tipoUser.avaliador
    )


class IsAdmin(BasePermission):
    """Apenas administradores."""

    def has_permission(self, request, view):
        return is_admin(request.user)


class IsAdminOrReadOnly(BasePermission):
    """Leitura para qualquer autenticado; escrita apenas para administradores."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return is_admin(request.user)


class IsAdminOrSelf(BasePermission):
    """Administrador acessa qualquer usuário; os demais apenas o próprio registro."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return is_admin(request.user) or obj.pk == request.user.pk


class IsAvaliadorDaEdicaoOrReadOnly(BasePermission):
    """
    Leitura para qualquer autenticado. Escrita em notas somente pelo avaliador
    (vínculo AvaliadorEdicao) dono da nota; administradores têm apenas leitura.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        if not is_avaliador(request.user):
            return False

        # Na criação (inclusive em lote) o vínculo informado deve ser do próprio usuário.
        if request.method == "POST":
            avaliador_id = request.data.get("avaliador")
            if avaliador_id in (None, ""):
                return True  # o serializer devolve 400 por campo obrigatório
            try:
                return AvaliadorEdicao.objects.filter(
                    pk=avaliador_id, avaliador=request.user
                ).exists()
            except (TypeError, ValueError):
                return True  # id malformado: o serializer devolve 400
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.avaliador.avaliador_id == request.user.pk

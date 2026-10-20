from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """Limite mais rígido para tentativas de login (por IP)."""

    scope = "login"


class RegistroRateThrottle(AnonRateThrottle):
    """Limite para criação de contas (por IP)."""

    scope = "registro"

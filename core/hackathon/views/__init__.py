from .apoiador import ApoiadorViewSet
from .tipo_edicao import TipoEdicaoViewSet
from .user import UserViewSet
from .edicao import EdicaoViewSet
from .criterio import CriterioViewSet
from .tema import TemaViewSet
from .projeto import ProjetoViewSet
from .equipe import EquipeViewSet
from .nota import NotaViewSet
from .participanteEquipe import ParticipanteEquipeViewSet
from .avaliadorEdicao import AvaliadorEdicaoViewSet

__all__ = [
    "ApoiadorViewSet",
    "TipoEdicaoViewSet",
    "UserViewSet",
    "EdicaoViewSet",
    "CriterioViewSet",
    "TemaViewSet",
    "ProjetoViewSet",
    "EquipeViewSet",
    "NotaViewSet",
    "ParticipanteEquipeViewSet",
    "AvaliadorEdicaoViewSet",
]
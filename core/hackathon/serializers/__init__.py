from .apoiador import ApoiadorSerializer, ApoiadorListSerializer
from .tipo_edicao import TipoEdicaoSerializer
from .user import UserSerializer, UserListSerializer
from .edicao import EdicaoSerializer, EdicaoListSerializer
from .criterio import CriterioSerializer
from .tema import TemaSerializer
from .projeto import ProjetoListSerializer, ProjetoSerializer
from .equipe import EquipeListSerializer, EquipeSerializer
from .participanteEquipe import ParticipanteEquipeSerializer, ParticipanteEquipeListSerializer
from .token import CustomTokenObtainPairSerializer
from .nota import (
    NotaSerializer,
    NotaListSerializer,
    ItemNotaLoteSerializer,
    NotaLoteSerializer,
)
from .avaliadorEdicao import (
    AvaliadorSerializer,
    AvaliadorListSerializer,
    AvaliadorEdicaoSerializer,
    AvaliadorEdicaoListSerializer,
)

__all__ = [
    "ApoiadorSerializer",
    "ApoiadorListSerializer",
    "TipoEdicaoSerializer",
    "UserSerializer",
    "UserListSerializer",
    "EdicaoSerializer",
    "EdicaoListSerializer",
    "CriterioSerializer",
    "TemaSerializer",
    "ProjetoListSerializer", 
    "ProjetoSerializer",
    "EquipeListSerializer",
    "EquipeSerializer",
    "NotaSerializer",
    "NotaListSerializer",
    "ItemNotaLoteSerializer",
    "NotaLoteSerializer",
    "ParticipanteEquipeSerializer",
    "ParticipanteEquipeListSerializer",
    "AvaliadorSerializer",
    "AvaliadorListSerializer",
    "AvaliadorEdicaoSerializer",
    "AvaliadorEdicaoListSerializer",
    'CustomTokenObtainPairSerializer'
]
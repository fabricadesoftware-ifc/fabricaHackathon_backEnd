from .apoiador import ApoiadorSerializer, ApoiadorListSerializer
from .tipo_edicao import TipoEdicaoSerializer
from .tipo_user import TipoUserSerializer
from .user import UserSerializer, UserListSerializer
from .edicao import EdicaoSerializer, EdicaoListSerializer
from .criterio import CriterioSerializer
from .tema import TemaSerializer
from .projeto import ProjetoListSerializer, ProjetoSerializer
from .equipe import EquipeListSerializer, EquipeSerializer
from .participanteEquipe import ParticipanteEquipeSerializer, ParticipanteEquipeListSerializer
from .nota import NotaSerializer, NotaListSerializer

__all__ = [
    "ApoiadorSerializer",
    "ApoiadorListSerializer",
    "TipoEdicaoSerializer",
    "TipoUserSerializer",
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
    "ParticipanteEquipeSerializer",
    "ParticipanteEquipeListSerializer",
]
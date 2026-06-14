from .apoiador import ApoiadorSerializer, ApoiadorListSerializer
from .tipo_edicao import TipoEdicaoSerializer
from .tipo_user import TipoUserSerializer
from .edicao import EdicaoSerializer, EdicaoListSerializer
from .criterio import CriterioSerializer
from .tema import TemaSerializer
from .projeto import ProjetoListSerializer, ProjetoSerializer
from .equipe import EquipeListSerializer, EquipeSerializer

from .nota import NotaSerializer, NotaListSerializer
__all__ = [
    "ApoiadorSerializer",
    "ApoiadorListSerializer",
    "TipoEdicaoSerializer",
    "TipoUserSerializer",
    "EdicaoSerializer",
    "EdicaoListSerializer",
    "CriterioSerializer",
    "TemaSerializer",
    "ProjetoListSerializer", 
    "ProjetoSerializer",
    "EquipeListSerializer",
    "EquipeSerializer"
    "NotaSerializer",
    "NotaListSerializer",
]
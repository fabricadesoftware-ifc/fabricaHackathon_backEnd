from rest_framework.exceptions import PermissionDenied

MENSAGEM_FINALIZADA = 'A edição está finalizada: os dados ficam somente para leitura.'


def bloquear_se_finalizada(edicao):
    if edicao is not None and edicao.status == 'FINALIZADO':
        raise PermissionDenied(MENSAGEM_FINALIZADA)


class BloqueiaEdicaoFinalizadaMixin:
    """
    Escritas (inclusive de administradores) são recusadas com 403 quando a edição
    do registro está FINALIZADO. As views informam como chegar na edição:
    `edicao_da_instancia` (registro existente) e `edicao_dos_dados` (dados validados).
    """

    def edicao_da_instancia(self, instance):
        return instance.edicao

    def edicao_dos_dados(self, validated_data):
        return validated_data.get('edicao')

    def perform_create(self, serializer):
        bloquear_se_finalizada(self.edicao_dos_dados(serializer.validated_data))
        super().perform_create(serializer)

    def perform_update(self, serializer):
        bloquear_se_finalizada(self.edicao_da_instancia(serializer.instance))
        bloquear_se_finalizada(self.edicao_dos_dados(serializer.validated_data))
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        bloquear_se_finalizada(self.edicao_da_instancia(instance))
        super().perform_destroy(instance)

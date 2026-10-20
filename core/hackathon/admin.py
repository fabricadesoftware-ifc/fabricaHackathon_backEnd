from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Apoiador,
    TipoEdicao,
    User,
    Edicao,
    Criterio,
    Tema,
    Projeto,
    Equipe,
    Nota,
    ParticipanteEquipe,
    AvaliadorEdicao,
    SolicitacaoPerfil,
)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informações do Hackathon', {'fields': ('tipoUser',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informações do Hackathon', {'fields': ('tipoUser',)}),
    )
    list_display = ['username', 'email', 'first_name', 'last_name', 'tipoUser', 'is_staff']
    list_filter = ['tipoUser', 'is_staff', 'is_superuser', 'is_active']

@admin.register(SolicitacaoPerfil)
class SolicitacaoPerfilAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'perfil_solicitado', 'status', 'criada_em', 'decidida_em', 'decidida_por']
    list_filter = ['status', 'perfil_solicitado']
    search_fields = ['usuario__email', 'usuario__username']
    readonly_fields = ['criada_em', 'decidida_em', 'decidida_por']
    actions = ['aprovar_solicitacoes', 'recusar_solicitacoes']

    def _decidir_em_massa(self, request, queryset, metodo, rotulo):
        decididas = 0
        for solicitacao in queryset.select_related('usuario').filter(status=SolicitacaoPerfil.Status.PENDENTE):
            getattr(solicitacao, metodo)(request.user)
            decididas += 1
        self.message_user(request, f'{decididas} solicitação(ões) {rotulo}.')

    @admin.action(description='Aprovar solicitações selecionadas (apenas pendentes)')
    def aprovar_solicitacoes(self, request, queryset):
        self._decidir_em_massa(request, queryset, 'aprovar', 'aprovada(s)')

    @admin.action(description='Recusar solicitações selecionadas (apenas pendentes)')
    def recusar_solicitacoes(self, request, queryset):
        self._decidir_em_massa(request, queryset, 'recusar', 'recusada(s)')


admin.site.register(Apoiador)
admin.site.register(TipoEdicao)
admin.site.register(Edicao)
admin.site.register(Criterio)
admin.site.register(Tema)
admin.site.register(Projeto)
admin.site.register(Equipe)
admin.site.register(Nota)
admin.site.register(ParticipanteEquipe)
admin.site.register(AvaliadorEdicao)

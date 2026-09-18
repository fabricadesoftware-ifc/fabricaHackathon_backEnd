from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Apoiador, TipoEdicao, User, Edicao, Criterio, Tema, Projeto, Equipe, Nota, ParticipanteEquipe

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

admin.site.register(Apoiador)
admin.site.register(TipoEdicao)
admin.site.register(Edicao)
admin.site.register(Criterio)
admin.site.register(Tema)
admin.site.register(Projeto)
admin.site.register(Equipe)
admin.site.register(Nota)
admin.site.register(ParticipanteEquipe)

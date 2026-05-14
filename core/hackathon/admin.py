from django.contrib import admin
from .models import Apoiador, TipoEdicao, TipoUser, Edicao


admin.site.register(Apoiador)
admin.site.register(TipoEdicao)
admin.site.register(TipoUser)
admin.site.register(Edicao)
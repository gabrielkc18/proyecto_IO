from django.contrib import admin

from config.admin import SuperuserOnlyAdminMixin
from .models import Problema


@admin.register(Problema)
class ProblemaAdmin(SuperuserOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "nombre",
        "sentido_objetivo",
        "estado",
        "fecha_creacion",
    )
    list_filter = ("sentido_objetivo", "estado")
    search_fields = ("nombre", "descripcion")
    ordering = ("-fecha_creacion",)

    def get_readonly_fields(self, _request, obj=None):
        return ("workspace",) if obj is not None else ()
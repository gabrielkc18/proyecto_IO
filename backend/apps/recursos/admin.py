from django.contrib import admin

from config.admin import SuperuserOnlyAdminMixin
from .models import Recurso, ConsumoRecurso


@admin.register(Recurso)
class RecursoAdmin(SuperuserOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "nombre",
        "problema",
        "unidad_medida",
        "disponibilidad",
        "activo",
    )
    list_filter = ("activo", "problema")
    search_fields = ("nombre", "unidad_medida")
    list_select_related = ("problema",)

    def get_readonly_fields(self, _request, obj=None):
        return ("problema",) if obj is not None else ()


@admin.register(ConsumoRecurso)
class ConsumoRecursoAdmin(SuperuserOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "producto",
        "recurso",
        "cantidad_por_unidad",
    )
    search_fields = (
        "producto__codigo",
        "producto__nombre",
        "recurso__nombre",
    )
    list_select_related = ("producto", "recurso")

    def get_readonly_fields(self, _request, obj=None):
        return ("producto", "recurso") if obj is not None else ()
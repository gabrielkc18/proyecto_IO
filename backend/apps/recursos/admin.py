from django.contrib import admin
from .models import Recurso, ConsumoRecurso


@admin.register(Recurso)
class RecursoAdmin(admin.ModelAdmin):
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


@admin.register(ConsumoRecurso)
class ConsumoRecursoAdmin(admin.ModelAdmin):
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
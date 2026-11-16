from django.contrib import admin
from .models import ResultadoProducto, ResultadoRecurso


@admin.register(ResultadoProducto)
class ResultadoProductoAdmin(admin.ModelAdmin):
    list_display = (
        "ejecucion",
        "producto",
        "nombre_producto",
        "cantidad",
        "utilidad_unitaria",
        "utilidad_aportada",
    )
    search_fields = ("nombre_producto", "producto__codigo")
    list_select_related = ("ejecucion", "producto")


@admin.register(ResultadoRecurso)
class ResultadoRecursoAdmin(admin.ModelAdmin):
    list_display = (
        "ejecucion",
        "recurso",
        "nombre_recurso",
        "disponibilidad",
        "consumo_total",
        "holgura",
        "estado_uso",
    )
    list_filter = ("estado_uso",)
    search_fields = ("nombre_recurso", "recurso__nombre")
    list_select_related = ("ejecucion", "recurso")
from django.contrib import admin

from config.admin import ReadOnlyRecordsAdminMixin
from .models import AnalisisIA


@admin.register(AnalisisIA)
class AnalisisIAAdmin(ReadOnlyRecordsAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "ejecucion",
        "tipo_analisis",
        "modelo_ia",
        "fecha_generacion",
    )
    list_filter = ("tipo_analisis", "modelo_ia")
    search_fields = ("pregunta", "contenido", "modelo_ia")
    list_select_related = ("ejecucion",)
    readonly_fields = ("fecha_generacion",)
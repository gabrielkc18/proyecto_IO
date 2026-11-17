from django.contrib import admin

from config.admin import ReadOnlyRecordsAdminMixin
from .models import Ejecucion


@admin.register(Ejecucion)
class EjecucionAdmin(ReadOnlyRecordsAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "problema",
        "fecha_inicio",
        "fecha_fin",
        "estado_proceso",
        "estado_solver",
        "utilidad_total",
    )
    list_filter = ("estado_proceso", "estado_solver")
    search_fields = ("problema__nombre", "solver_nombre")
    list_select_related = ("problema",)
from django.contrib import admin

from config.admin import SuperuserOnlyAdminMixin
from .models import Producto


@admin.register(Producto)
class ProductoAdmin(SuperuserOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "codigo",
        "nombre",
        "problema",
        "utilidad_unitaria",
        "activo",
    )
    list_filter = ("activo", "problema")
    search_fields = ("codigo", "nombre")
    list_select_related = ("problema",)

    def get_readonly_fields(self, _request, obj=None):
        return ("problema",) if obj is not None else ()
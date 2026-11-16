from django.contrib import admin
from .models import Producto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
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
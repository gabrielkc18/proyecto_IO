from django.contrib import admin
from .models import Problema


@admin.register(Problema)
class ProblemaAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "sentido_objetivo",
        "estado",
        "fecha_creacion",
    )
    list_filter = ("sentido_objetivo", "estado")
    search_fields = ("nombre", "descripcion")
    ordering = ("-fecha_creacion",)
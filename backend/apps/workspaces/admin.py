from django.contrib import admin

from .models import Workspace, WorkspaceMembership


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "propietario", "fecha_creacion")
    search_fields = ("nombre", "propietario__username")
    list_filter = ("fecha_creacion",)


@admin.register(WorkspaceMembership)
class WorkspaceMembershipAdmin(admin.ModelAdmin):
    list_display = ("workspace", "usuario", "rol", "fecha_creacion")
    list_filter = ("rol",)
    search_fields = ("workspace__nombre", "usuario__username")
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import transaction

from config.admin import SuperuserOnlyAdminMixin

from .models import Workspace, WorkspaceMembership


@admin.register(Workspace)
class WorkspaceAdmin(SuperuserOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("id", "nombre", "propietario", "fecha_creacion")
    search_fields = ("nombre", "propietario__username")
    list_filter = ("fecha_creacion",)

    def get_readonly_fields(self, _request, obj=None):
        if obj is not None:
            return ("propietario",)
        return ()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "propietario":
            kwargs["queryset"] = get_user_model().objects.filter(
                is_active=True,
            )
        return super().formfield_for_foreignkey(
            db_field,
            request,
            **kwargs,
        )

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            super().save_model(request, obj, form, change)
            if not change:
                WorkspaceMembership.objects.create(
                    workspace=obj,
                    usuario=obj.propietario,
                    rol=WorkspaceMembership.Rol.OWNER,
                )


@admin.register(WorkspaceMembership)
class WorkspaceMembershipAdmin(SuperuserOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("workspace", "usuario", "rol", "fecha_creacion")
    list_filter = ("rol",)
    search_fields = ("workspace__nombre", "usuario__username")
    readonly_fields = ("workspace", "usuario", "rol", "fecha_creacion")
    actions = None

    def has_add_permission(self, _request):
        return False

    def has_delete_permission(self, _request, _obj=None):
        return False
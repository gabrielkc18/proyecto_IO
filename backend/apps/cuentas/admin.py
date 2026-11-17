from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.db import transaction

from config.admin import SuperuserOnlyAdminMixin
from apps.workspaces.services import obtener_o_crear_workspace_personal

from .models import PerfilCuenta


User = get_user_model()


class PerfilCuentaInline(admin.StackedInline):
    model = PerfilCuenta
    can_delete = False
    extra = 0
    readonly_fields = (
        "correo_verificado",
        "fecha_creacion",
        "fecha_actualizacion",
    )


class PlanificaUserAdmin(SuperuserOnlyAdminMixin, UserAdmin):
    inlines = (PerfilCuentaInline,)

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            correo_anterior = None
            if change:
                correo_anterior = User.objects.filter(pk=obj.pk).values_list(
                    "email",
                    flat=True,
                ).first()
            super().save_model(request, obj, form, change)
            if not change:
                PerfilCuenta.objects.get_or_create(
                    usuario=obj,
                    defaults={"correo_verificado": True},
                )
                obtener_o_crear_workspace_personal(obj)
            elif correo_anterior != obj.email:
                perfil, _ = PerfilCuenta.objects.get_or_create(usuario=obj)
                perfil.correo_verificado = False
                perfil.save(
                    update_fields=["correo_verificado", "fecha_actualizacion"],
                )


try:
    admin.site.unregister(User)
except NotRegistered:
    pass
admin.site.register(User, PlanificaUserAdmin)


@admin.register(PerfilCuenta)
class PerfilCuentaAdmin(SuperuserOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("usuario", "correo_verificado", "fecha_actualizacion")
    search_fields = ("usuario__username", "usuario__email")
    list_filter = ("correo_verificado",)
    readonly_fields = (
        "usuario",
        "correo_verificado",
        "fecha_creacion",
        "fecha_actualizacion",
    )

    def has_add_permission(self, _request):
        return False

    def has_delete_permission(self, _request, _obj=None):
        return False

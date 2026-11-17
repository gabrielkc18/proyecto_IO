from django.urls import path

from .views import (
    CambioContrasenaAPIView,
    ConfirmarRestablecimientoAPIView,
    PerfilAPIView,
    RegistroAPIView,
    ReenviarVerificacionAPIView,
    SolicitarRestablecimientoAPIView,
    VerificarCorreoAPIView,
)


urlpatterns = [
    path("auth/registro/", RegistroAPIView.as_view(), name="account-register"),
    path("auth/perfil/", PerfilAPIView.as_view(), name="account-profile"),
    path(
        "auth/cambiar-contrasena/",
        CambioContrasenaAPIView.as_view(),
        name="account-change-password",
    ),
    path(
        "auth/verificar-correo/",
        VerificarCorreoAPIView.as_view(),
        name="account-verify-email",
    ),
    path(
        "auth/verificar-correo/reenviar/",
        ReenviarVerificacionAPIView.as_view(),
        name="account-resend-verification",
    ),
    path(
        "auth/recuperar-contrasena/",
        SolicitarRestablecimientoAPIView.as_view(),
        name="account-password-reset-request",
    ),
    path(
        "auth/recuperar-contrasena/confirmar/",
        ConfirmarRestablecimientoAPIView.as_view(),
        name="account-password-reset-confirm",
    ),
]

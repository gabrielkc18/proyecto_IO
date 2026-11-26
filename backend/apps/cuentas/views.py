import logging
import smtplib
from binascii import Error as BinasciiError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import (
    ImproperlyConfigured,
    ValidationError as DjangoValidationError,
)
from django.core.mail import BadHeaderError, send_mail
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import format_html
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from drf_spectacular.utils import (
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers, status
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.utils import get_md5_hash_password
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.workspaces.services import obtener_o_crear_workspace_personal

from .models import PerfilCuenta
from .serializers import (
    CambioContrasenaSerializer,
    ConfirmarTokenSerializer,
    IdentificadorCuentaSerializer,
    PerfilSerializer,
    RegistroSerializer,
    RestablecerContrasenaSerializer,
)


logger = logging.getLogger(__name__)
User = get_user_model()
MENSAJE_RECUPERACION = (
    "Si la cuenta puede recuperar el acceso, recibirá instrucciones "
    "en el correo registrado."
)
REFRESH_COOKIE_NAME = "planificai_refresh"
REFRESH_COOKIE_PATH = "/api/token/"
REFRESH_COOKIE_HEADER = "HTTP_X_REFRESH_TOKEN_COOKIE"


def _detail_response_schema(name):
    return inline_serializer(
        name=name,
        fields={"detail": serializers.CharField()},
    )


def _establecer_cookie_refresh(response, token):
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        token,
        max_age=int(api_settings.REFRESH_TOKEN_LIFETIME.total_seconds()),
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite="Lax",
        path=REFRESH_COOKIE_PATH,
    )


def _correo_verificado(usuario):
    perfil = PerfilCuenta.objects.filter(usuario=usuario).first()
    return perfil is None or perfil.correo_verificado


def _url_accion(request, setting_name, endpoint_name, uid, token):
    base_url = getattr(settings, setting_name)
    if not base_url:
        base_url = request.build_absolute_uri(reverse(endpoint_name))
    parts = urlsplit(base_url)
    query = dict(parse_qsl(parts.query))
    query.update({"uid": uid, "token": token})
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
    )


def _enviar_correo(usuario, asunto, mensaje):
    if not usuario.email:
        return False
    try:
        sent_count = send_mail(
            subject=asunto,
            message=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[usuario.email],
            fail_silently=False,
        )
    except (
        OSError,
        smtplib.SMTPException,
        BadHeaderError,
        ImproperlyConfigured,
    ) as error:
        logger.warning(
            "No se pudo enviar un correo de cuenta (%s).",
            type(error).__name__,
        )
        return False
    if sent_count != 1:
        logger.warning("El backend de correo no confirmó el envío.")
        return False
    return True


def _obtener_usuario_de_token(uid):
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        return User.objects.filter(pk=user_id).first()
    except (TypeError, ValueError, UnicodeDecodeError, BinasciiError):
        return None


class TokenDeRenovacionSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        refresh = self.token_class(attrs["refresh"])
        user_id = refresh.get(api_settings.USER_ID_CLAIM)
        usuario = User.objects.filter(
            **{api_settings.USER_ID_FIELD: user_id}
        ).first()
        if usuario is None or not usuario.is_active:
            raise AuthenticationFailed("Credenciales inválidas.")
        if api_settings.CHECK_REVOKE_TOKEN:
            token_hash = refresh.get(api_settings.REVOKE_TOKEN_CLAIM)
            if token_hash != get_md5_hash_password(usuario.password):
                raise AuthenticationFailed("El token fue revocado.")
        return super().validate(attrs)


class AccountTokenObtainPairView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_login"

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if request.META.get(REFRESH_COOKIE_HEADER) == "1":
            refresh = response.data.pop("refresh", None)
            if refresh:
                _establecer_cookie_refresh(response, refresh)
        return response


class AccountTokenRefreshView(TokenRefreshView):
    serializer_class = TokenDeRenovacionSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_refresh"

    def post(self, request, *args, **kwargs):
        if request.META.get(REFRESH_COOKIE_HEADER) != "1":
            return super().post(request, *args, **kwargs)

        payload = request.data.copy()
        refresh = payload.get("refresh") or request.COOKIES.get(
            REFRESH_COOKIE_NAME
        )
        if refresh:
            payload["refresh"] = refresh

        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        response = Response(serializer.validated_data, status=status.HTTP_200_OK)
        rotated_refresh = response.data.pop("refresh", refresh)
        if rotated_refresh:
            _establecer_cookie_refresh(response, rotated_refresh)
        return response

    def handle_exception(self, exc):
        response = super().handle_exception(exc)
        if (
            self.request.META.get(REFRESH_COOKIE_HEADER) == "1"
            and response.status_code in {
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_401_UNAUTHORIZED,
            }
        ):
            response.delete_cookie(
                REFRESH_COOKIE_NAME,
                path=REFRESH_COOKIE_PATH,
                samesite="Lax",
            )
        return response


class CuentaPublicaAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]


class RegistroAPIView(CuentaPublicaAPIView):
    throttle_scope = "registration"

    @extend_schema(
        tags=["Cuentas"],
        request=RegistroSerializer,
        responses={
            201: inline_serializer(
                name="RegistroResponse",
                fields={
                    "detail": serializers.CharField(),
                    "workspace_id": serializers.IntegerField(),
                },
            ),
            400: OpenApiResponse(description="Datos de registro inválidos."),
        },
    )
    def post(self, request):
        serializer = RegistroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        try:
            with transaction.atomic():
                usuario = User.objects.create_user(
                    username=datos["username"],
                    email=datos["email"],
                    password=datos["password"],
                    first_name=datos.get("first_name", ""),
                    last_name=datos.get("last_name", ""),
                )
                PerfilCuenta.objects.create(
                    usuario=usuario,
                    correo_verificado=False,
                )
                workspace = obtener_o_crear_workspace_personal(usuario)
        except IntegrityError:
            return Response(
                {"detail": "No fue posible completar el registro."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ValueError as error:
            raise ValidationError(
                {"detail": "No fue posible completar el registro."}
            ) from error

        return Response(
            {
                "detail": "La cuenta fue creada. Ya puedes iniciar sesión.",
                "workspace_id": workspace.pk,
            },
            status=status.HTTP_201_CREATED,
        )

    @staticmethod
    def _enviar_verificacion(request, usuario):
        uid = urlsafe_base64_encode(force_bytes(usuario.pk))
        token = default_token_generator.make_token(usuario)
        url = _url_accion(
            request,
            "ACCOUNT_EMAIL_VERIFICATION_URL",
            "account-verify-email",
            uid,
            token,
        )
        return _enviar_correo(
            usuario,
            "Verifica tu cuenta de PlanificaIO",
            "Para verificar tu cuenta, abre este enlace y confirma la "
            f"operación desde la aplicación:\n{url}",
        )


class PerfilAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @extend_schema(
        tags=["Cuentas"],
        responses={200: PerfilSerializer},
    )
    def get(self, request):
        return Response(PerfilSerializer(request.user).data)

    @extend_schema(
        tags=["Cuentas"],
        request=PerfilSerializer,
        responses={200: PerfilSerializer},
    )
    def patch(self, request):
        serializer = PerfilSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(PerfilSerializer(request.user).data)


class CambioContrasenaAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_change"

    @extend_schema(
        tags=["Cuentas"],
        request=CambioContrasenaSerializer,
        responses={
            200: _detail_response_schema("CambioContrasenaResponse"),
            400: OpenApiResponse(description="Credenciales o datos inválidos."),
        },
    )
    def post(self, request):
        serializer = CambioContrasenaSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            usuario = User.objects.select_for_update().get(pk=request.user.pk)
            if not usuario.check_password(
                serializer.validated_data["current_password"]
            ):
                raise ValidationError(
                    {"current_password": "La contraseña actual no es válida."}
                )
            usuario.set_password(serializer.validated_data["new_password"])
            usuario.save(update_fields=["password"])
        return Response(
            {"detail": "La contraseña fue actualizada. Inicia sesión de nuevo."}
        )


class CerrarSesionAPIView(CuentaPublicaAPIView):
    @extend_schema(
        tags=["Cuentas"],
        responses={204: OpenApiResponse(description="Sesión cerrada.")},
    )
    def post(self, request):
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(
            REFRESH_COOKIE_NAME,
            path=REFRESH_COOKIE_PATH,
            samesite="Lax",
        )
        return response


class VerificarCorreoAPIView(CuentaPublicaAPIView):
    throttle_scope = "email_verification"

    @extend_schema(
        tags=["Cuentas"],
        responses={(200, "text/html"): OpenApiTypes.STR},
    )
    def get(self, request):
        return HttpResponse(
            format_html(
                '<main><h1>Verificar correo</h1>'
                '<p>Confirma para activar el inicio de sesión.</p>'
                '<form method="post" action="{}">'
                '<input type="hidden" name="uid" value="{}">'
                '<input type="hidden" name="token" value="{}">'
                '<button type="submit">Verificar correo</button>'
                "</form></main>",
                reverse("account-verify-email"),
                request.query_params.get("uid", ""),
                request.query_params.get("token", ""),
            )
        )

    @extend_schema(
        tags=["Cuentas"],
        request=ConfirmarTokenSerializer,
        responses={
            200: _detail_response_schema("VerificarCorreoResponse"),
            400: OpenApiResponse(description="El enlace no es válido o expiró."),
        },
    )
    def post(self, request):
        serializer = ConfirmarTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = _obtener_usuario_de_token(serializer.validated_data["uid"])
        token = serializer.validated_data["token"]
        if (
            usuario is None
            or not usuario.is_active
            or not default_token_generator.check_token(usuario, token)
        ):
            raise ValidationError(
                {"detail": "El enlace de verificación no es válido o expiró."}
            )
        perfil, _ = PerfilCuenta.objects.get_or_create(usuario=usuario)
        if perfil.correo_verificado:
            return Response({"detail": "El correo ya está verificado."})
        perfil.correo_verificado = True
        perfil.save(update_fields=["correo_verificado", "fecha_actualizacion"])
        return Response({"detail": "El correo fue verificado."})


class ReenviarVerificacionAPIView(CuentaPublicaAPIView):
    throttle_scope = "email_verification"

    @extend_schema(
        tags=["Cuentas"],
        request=IdentificadorCuentaSerializer,
        responses={202: _detail_response_schema("ReenviarVerificacionResponse")},
    )
    def post(self, request):
        serializer = IdentificadorCuentaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = User.objects.filter(
            username=serializer.validated_data["username"],
            is_active=True,
        ).first()
        if (
            usuario is not None
            and not _correo_verificado(usuario)
            and usuario.email
        ):
            RegistroAPIView._enviar_verificacion(request, usuario)
        return Response(
            {"detail": "Si la cuenta requiere verificación, recibirá un correo."},
            status=status.HTTP_202_ACCEPTED,
        )


class SolicitarRestablecimientoAPIView(CuentaPublicaAPIView):
    throttle_scope = "password_recovery"

    @extend_schema(
        tags=["Cuentas"],
        request=IdentificadorCuentaSerializer,
        responses={202: _detail_response_schema("SolicitarRestablecimientoResponse")},
    )
    def post(self, request):
        serializer = IdentificadorCuentaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = User.objects.filter(
            username=serializer.validated_data["username"],
            is_active=True,
        ).first()
        if (
            usuario is not None
            and usuario.email
        ):
            uid = urlsafe_base64_encode(force_bytes(usuario.pk))
            token = default_token_generator.make_token(usuario)
            url = _url_accion(
                request,
                "ACCOUNT_PASSWORD_RESET_URL",
                "account-password-reset-confirm",
                uid,
                token,
            )
            _enviar_correo(
                usuario,
                "Restablece tu contraseña de PlanificaIO",
                "Para elegir una contraseña nueva, abre este enlace:\n"
                f"{url}",
            )
        return Response(
            {"detail": MENSAJE_RECUPERACION},
            status=status.HTTP_202_ACCEPTED,
        )


class ConfirmarRestablecimientoAPIView(CuentaPublicaAPIView):
    throttle_scope = "password_recovery"

    @extend_schema(
        tags=["Cuentas"],
        responses={(200, "text/html"): OpenApiTypes.STR},
    )
    def get(self, request):
        return HttpResponse(
            format_html(
                '<main><h1>Restablecer contraseña</h1>'
                '<form method="post" action="{}">'
                '<input type="hidden" name="uid" value="{}">'
                '<input type="hidden" name="token" value="{}">'
                '<label>Nueva contraseña <input type="password" '
                'name="new_password" maxlength="128" required></label>'
                '<label>Confirmar contraseña <input type="password" '
                'name="new_password_confirm" maxlength="128" required></label>'
                '<button type="submit">Restablecer</button>'
                "</form></main>",
                reverse("account-password-reset-confirm"),
                request.query_params.get("uid", ""),
                request.query_params.get("token", ""),
            )
        )

    @extend_schema(
        tags=["Cuentas"],
        request=RestablecerContrasenaSerializer,
        responses={
            200: _detail_response_schema("ConfirmarRestablecimientoResponse"),
            400: OpenApiResponse(description="El enlace o la contraseña no es válido."),
        },
    )
    def post(self, request):
        serializer = RestablecerContrasenaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = _obtener_usuario_de_token(serializer.validated_data["uid"])
        token = serializer.validated_data["token"]
        if (
            usuario is None
            or not usuario.is_active
            or not default_token_generator.check_token(usuario, token)
        ):
            raise ValidationError(
                {"detail": "El enlace de recuperación no es válido o expiró."}
            )
        try:
            validate_password(
                serializer.validated_data["new_password"],
                user=usuario,
            )
        except DjangoValidationError as error:
            raise ValidationError(
                {"new_password": list(error.messages)}
            ) from error
        with transaction.atomic():
            usuario = User.objects.select_for_update().get(pk=usuario.pk)
            if (
                not usuario.is_active
                or not default_token_generator.check_token(usuario, token)
            ):
                raise ValidationError(
                    {"detail": "El enlace de recuperación no es válido o expiró."}
                )
            usuario.set_password(serializer.validated_data["new_password"])
            usuario.save(update_fields=["password"])
        return Response(
            {"detail": "La contraseña fue restablecida. Inicia sesión de nuevo."}
        )

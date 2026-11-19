import re
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core import mail
from django.test import RequestFactory, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.workspaces.models import Workspace, WorkspaceMembership
from apps.cuentas.admin import PlanificaUserAdmin
from apps.cuentas.models import PerfilCuenta
from apps.cuentas.views import recuperacion_token, verificacion_token


User = get_user_model()


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    ACCOUNT_EMAIL_VERIFICATION_URL="",
    ACCOUNT_PASSWORD_RESET_URL="",
)
class CuentaAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.register_url = reverse("account-register")
        self.verify_url = reverse("account-verify-email")
        self.resend_verification_url = reverse("account-resend-verification")
        self.login_url = reverse("token_obtain_pair")
        self.reset_request_url = reverse("account-password-reset-request")
        self.reset_confirm_url = reverse("account-password-reset-confirm")

    def register_payload(self, username="nuevo_usuario"):
        return {
            "username": username,
            "email": f"{username}@example.test",
            "password": "PlanificaFuerte2026!",
            "password_confirm": "PlanificaFuerte2026!",
        }

    @staticmethod
    def token_from_last_email():
        match = re.search(r"https?://\S+", mail.outbox[-1].body)
        if match is None:
            raise AssertionError("El correo no contiene un enlace.")
        return parse_qs(urlsplit(match.group()).query)

    def test_tokens_de_cuenta_se_validan_por_proposito(self):
        usuario = User.objects.create_user(username="cuenta_tokens")
        token_correo = verificacion_token.make_token(usuario)
        token_contrasena = recuperacion_token.make_token(usuario)

        self.assertTrue(verificacion_token.check_token(usuario, token_correo))
        self.assertTrue(recuperacion_token.check_token(usuario, token_contrasena))
        self.assertFalse(verificacion_token.check_token(usuario, token_contrasena))
        self.assertFalse(recuperacion_token.check_token(usuario, token_correo))

    def test_registration_atomically_creates_unprivileged_account_workspace_owner(self):
        response = self.client.post(
            self.register_url,
            self.register_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="nuevo_usuario")
        self.assertTrue(user.check_password("PlanificaFuerte2026!"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.perfil_cuenta.correo_verificado)
        workspace = Workspace.objects.get(propietario=user)
        self.assertEqual(
            WorkspaceMembership.objects.get(
                workspace=workspace,
                usuario=user,
            ).rol,
            WorkspaceMembership.Rol.OWNER,
        )
        self.assertEqual(len(mail.outbox), 1)

    def test_registration_rejects_bad_password_and_duplicate_username_without_partial_rows(self):
        bad_payload = self.register_payload()
        bad_payload["password_confirm"] = "otra"
        response = self.client.post(
            self.register_url,
            bad_payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="nuevo_usuario").exists())

        response = self.client.post(
            self.register_url,
            self.register_payload(),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        workspace_count = Workspace.objects.count()

        response = self.client.post(
            self.register_url,
            self.register_payload(),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Workspace.objects.count(), workspace_count)
        self.assertEqual(
            WorkspaceMembership.objects.filter(
                usuario__username="nuevo_usuario",
            ).count(),
            1,
        )

    @patch(
        "apps.cuentas.views.obtener_o_crear_workspace_personal",
        side_effect=RuntimeError("fallo simulado"),
    )
    def test_registration_rolls_back_user_and_profile_if_workspace_creation_fails(
        self,
        _mock_workspace,
    ):
        with self.assertRaises(RuntimeError):
            self.client.post(
                self.register_url,
                self.register_payload(),
                format="json",
            )

        self.assertFalse(User.objects.filter(username="nuevo_usuario").exists())
        self.assertFalse(
            PerfilCuenta.objects.filter(
                usuario__username="nuevo_usuario",
            ).exists()
        )

    def test_unverified_account_cannot_obtain_jwt_until_email_is_verified(self):
        self.client.post(
            self.register_url,
            self.register_payload(),
            format="json",
        )
        credentials = {
            "username": "nuevo_usuario",
            "password": "PlanificaFuerte2026!",
        }
        response = self.client.post(self.login_url, credentials, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        token_data = self.token_from_last_email()
        response = self.client.post(
            self.verify_url,
            {"uid": token_data["uid"][0], "token": token_data["token"][0]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            PerfilCuenta.objects.get(
                usuario__username="nuevo_usuario",
            ).correo_verificado
        )

        response = self.client.post(self.login_url, credentials, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_verification_rejects_invalid_token_without_activating_profile(self):
        self.client.post(
            self.register_url,
            self.register_payload(),
            format="json",
        )
        token_data = self.token_from_last_email()
        response = self.client.post(
            self.verify_url,
            {"uid": token_data["uid"][0], "token": "invalid"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            PerfilCuenta.objects.get(
                usuario__username="nuevo_usuario",
            ).correo_verificado
        )

    def test_resend_verification_does_not_disclose_account_existence(self):
        self.client.post(
            self.register_url,
            self.register_payload(),
            format="json",
        )
        existing = self.client.post(
            self.resend_verification_url,
            {"username": "nuevo_usuario"},
            format="json",
        )
        unknown = self.client.post(
            self.resend_verification_url,
            {"username": "no_existe"},
            format="json",
        )

        self.assertEqual(existing.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(unknown.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(existing.data, unknown.data)
        self.assertEqual(len(mail.outbox), 2)

        token_data = self.token_from_last_email()
        verification = self.client.post(
            self.verify_url,
            {"uid": token_data["uid"][0], "token": token_data["token"][0]},
            format="json",
        )
        self.assertEqual(verification.status_code, status.HTTP_200_OK)

    def test_password_recovery_response_does_not_disclose_account_existence(self):
        user = User.objects.create_user(
            username="recuperacion",
            email="recovery@example.test",
            password="ClaveFuerte2026!",
        )
        PerfilCuenta.objects.create(usuario=user, correo_verificado=True)

        existing = self.client.post(
            self.reset_request_url,
            {"username": "recuperacion"},
            format="json",
        )
        unknown = self.client.post(
            self.reset_request_url,
            {"username": "no_existe"},
            format="json",
        )

        self.assertEqual(existing.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(unknown.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(existing.data, unknown.data)
        self.assertEqual(len(mail.outbox), 1)

        token_data = self.token_from_last_email()
        response = self.client.post(
            self.reset_confirm_url,
            {
                "uid": token_data["uid"][0],
                "token": token_data["token"][0],
                "new_password": "OtraClaveSegura2026!",
                "new_password_confirm": "OtraClaveSegura2026!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password("OtraClaveSegura2026!"))

    def test_password_recovery_revokes_existing_access_and_refresh_tokens(self):
        user = User.objects.create_user(
            username="recuperacion_tokens",
            email="recovery@example.test",
            password="ClaveFuerte2026!",
        )
        PerfilCuenta.objects.create(usuario=user, correo_verificado=True)
        tokens = self.client.post(
            self.login_url,
            {
                "username": user.username,
                "password": "ClaveFuerte2026!",
            },
            format="json",
        )
        self.assertEqual(tokens.status_code, status.HTTP_200_OK)

        self.client.post(
            self.reset_request_url,
            {"username": user.username},
            format="json",
        )
        token_data = self.token_from_last_email()
        response = self.client.post(
            self.reset_confirm_url,
            {
                "uid": token_data["uid"][0],
                "token": token_data["token"][0],
                "new_password": "OtraClaveSegura2026!",
                "new_password_confirm": "OtraClaveSegura2026!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {tokens.data['access']}",
        )
        self.assertEqual(
            self.client.get(reverse("account-profile")).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        refresh_response = self.client.post(
            reverse("token_refresh"),
            {"refresh": tokens.data["refresh"]},
            format="json",
        )
        self.assertEqual(
            refresh_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_inactive_account_cannot_refresh_a_jwt(self):
        user = User.objects.create_user(
            username="inactivo",
            password="ClaveFuerte2026!",
        )
        PerfilCuenta.objects.create(usuario=user, correo_verificado=True)
        tokens = self.client.post(
            self.login_url,
            {
                "username": user.username,
                "password": "ClaveFuerte2026!",
            },
            format="json",
        )
        self.assertEqual(tokens.status_code, status.HTTP_200_OK)

        user.is_active = False
        user.save(update_fields=["is_active"])
        response = self.client.post(
            reverse("token_refresh"),
            {"refresh": tokens.data["refresh"]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_password_change_revokes_previous_access_and_refresh_tokens(self):
        user = User.objects.create_user(
            username="cambio_clave",
            password="ClaveFuerte2026!",
        )
        PerfilCuenta.objects.create(usuario=user, correo_verificado=True)
        tokens = self.client.post(
            self.login_url,
            {
                "username": user.username,
                "password": "ClaveFuerte2026!",
            },
            format="json",
        )
        self.assertEqual(tokens.status_code, status.HTTP_200_OK)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {tokens.data['access']}",
        )
        response = self.client.post(
            reverse("account-change-password"),
            {
                "current_password": "ClaveFuerte2026!",
                "new_password": "ClaveNuevaFuerte2026!",
                "new_password_confirm": "ClaveNuevaFuerte2026!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.client.get(reverse("account-profile")).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        refresh_response = self.client.post(
            reverse("token_refresh"),
            {"refresh": tokens.data["refresh"]},
            format="json",
        )
        self.assertEqual(
            refresh_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


class CreacionAdministrativaCuentaTests(APITestCase):
    def setUp(self):
        self.admin = PlanificaUserAdmin(User, admin.site)
        self.request = RequestFactory().post("/admin/auth/user/add/")

    def test_admin_creation_creates_verified_profile_and_personal_workspace(self):
        user = User(username="creado_admin")
        user.set_password("ClaveFuerte2026!")

        self.admin.save_model(self.request, user, form=None, change=False)

        self.assertTrue(user.perfil_cuenta.correo_verificado)
        self.assertEqual(
            WorkspaceMembership.objects.get(
                workspace__propietario=user,
                usuario=user,
            ).rol,
            WorkspaceMembership.Rol.OWNER,
        )

    def test_failed_workspace_provisioning_rolls_back_admin_user_creation(self):
        user = User(username="fallo_admin")
        user.set_password("ClaveFuerte2026!")

        with patch(
            "apps.cuentas.admin.obtener_o_crear_workspace_personal",
            side_effect=RuntimeError("fallo simulado"),
        ):
            with self.assertRaises(RuntimeError):
                self.admin.save_model(self.request, user, form=None, change=False)

        self.assertFalse(User.objects.filter(username="fallo_admin").exists())

    def test_admin_email_change_invalidates_previous_verification(self):
        user = User.objects.create_user(
            username="correo_admin",
            email="anterior@example.test",
            password="ClaveFuerte2026!",
        )
        profile = PerfilCuenta.objects.create(
            usuario=user,
            correo_verificado=True,
        )
        user.email = "nuevo@example.test"

        self.admin.save_model(self.request, user, form=None, change=True)

        profile.refresh_from_db()
        self.assertFalse(profile.correo_verificado)

    def test_admin_email_change_marks_legacy_account_unverified(self):
        user = User.objects.create_user(
            username="correo_legacy",
            email="anterior@example.test",
            password="ClaveFuerte2026!",
        )
        user.email = "nuevo@example.test"

        self.admin.save_model(self.request, user, form=None, change=True)

        self.assertFalse(user.perfil_cuenta.correo_verificado)

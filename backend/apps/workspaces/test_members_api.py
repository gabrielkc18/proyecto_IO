from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import IntegrityError, OperationalError
from django.test import RequestFactory
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.workspaces.admin import WorkspaceAdmin, WorkspaceMembershipAdmin
from apps.workspaces.models import Workspace, WorkspaceMembership
from apps.workspaces.test_utils import crear_workspace_prueba


User = get_user_model()


class WorkspaceMembersAPITests(APITestCase):

    def setUp(self):
        self.owner, self.workspace = crear_workspace_prueba(
            nombre="Workspace principal",
        )
        self.owner_membership = WorkspaceMembership.objects.get(
            workspace=self.workspace,
            usuario=self.owner,
        )

        self.admin = self.create_user("admin_member")
        self.admin_membership = self.create_membership(
            self.admin,
            WorkspaceMembership.Rol.ADMIN,
        )
        self.other_admin = self.create_user("other_admin")
        self.other_admin_membership = self.create_membership(
            self.other_admin,
            WorkspaceMembership.Rol.ADMIN,
        )
        self.editor = self.create_user("editor_member")
        self.editor_membership = self.create_membership(
            self.editor,
            WorkspaceMembership.Rol.EDITOR,
        )
        self.viewer = self.create_user("viewer_member")
        self.viewer_membership = self.create_membership(
            self.viewer,
            WorkspaceMembership.Rol.VIEWER,
        )

        self.external_user, self.external_workspace = (
            crear_workspace_prueba(nombre="Workspace externo")
        )
        self.external_membership = WorkspaceMembership.objects.get(
            workspace=self.external_workspace,
            usuario=self.external_user,
        )

        self.members_url = reverse(
            "workspace-members",
            kwargs={"workspace_id": self.workspace.pk},
        )

    def create_user(self, username, is_active=True):
        return User.objects.create_user(
            username=username,
            password="PruebaSegura123!",
            is_active=is_active,
        )

    def create_membership(self, user, role):
        return WorkspaceMembership.objects.create(
            workspace=self.workspace,
            usuario=user,
            rol=role,
        )

    def set_actor(self, user):
        self.client.force_authenticate(user=user)

    def member_detail_url(self, membership):
        return reverse(
            "workspace-member-detail",
            kwargs={
                "workspace_id": self.workspace.pk,
                "membership_id": membership.pk,
            },
        )

    def test_all_roles_can_list_members(self):
        for user in (self.owner, self.admin, self.editor, self.viewer):
            with self.subTest(user=user.username):
                self.set_actor(user)
                response = self.client.get(self.members_url)

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(len(response.data), 5)

    def test_listing_requires_authentication_and_workspace_membership(self):
        response = self.client.get(self.members_url)
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.set_actor(self.external_user)
        response = self.client.get(self.members_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_workspace_and_target_membership_are_scoped_to_url(self):
        self.set_actor(self.owner)

        external_workspace_url = reverse(
            "workspace-members",
            kwargs={"workspace_id": self.external_workspace.pk},
        )
        response = self.client.get(external_workspace_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        external_membership_url = reverse(
            "workspace-member-detail",
            kwargs={
                "workspace_id": self.workspace.pk,
                "membership_id": self.external_membership.pk,
            },
        )
        response = self.client.delete(external_membership_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.external_membership.refresh_from_db()

    def test_owner_adds_existing_active_user_and_ignores_body_workspace_id(self):
        self.set_actor(self.owner)
        user = self.create_user("new_editor")
        _, another_workspace = crear_workspace_prueba(
            nombre="Workspace que no debe seleccionarse",
        )

        response = self.client.post(
            self.members_url,
            {
                "username": user.username,
                "rol": WorkspaceMembership.Rol.EDITOR,
                "workspace_id": another_workspace.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        membership = WorkspaceMembership.objects.get(usuario=user)
        self.assertEqual(membership.workspace_id, self.workspace.pk)
        self.assertEqual(membership.rol, WorkspaceMembership.Rol.EDITOR)
        self.assertNotEqual(membership.workspace_id, another_workspace.pk)

    def test_owner_can_add_admin(self):
        self.set_actor(self.owner)
        user = self.create_user("new_admin")

        response = self.client.post(
            self.members_url,
            {"username": user.username, "rol": WorkspaceMembership.Rol.ADMIN},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            WorkspaceMembership.objects.filter(
                workspace=self.workspace,
                usuario=user,
                rol=WorkspaceMembership.Rol.ADMIN,
            ).exists()
        )

    def test_admin_can_add_editor_or_viewer_but_not_admin(self):
        self.set_actor(self.admin)
        for role in (
            WorkspaceMembership.Rol.EDITOR,
            WorkspaceMembership.Rol.VIEWER,
        ):
            with self.subTest(role=role):
                user = self.create_user(f"added_{role.lower()}")
                response = self.client.post(
                    self.members_url,
                    {"username": user.username, "rol": role},
                    format="json",
                )
                self.assertEqual(
                    response.status_code,
                    status.HTTP_201_CREATED,
                )

        forbidden_user = self.create_user("forbidden_admin")
        response = self.client.post(
            self.members_url,
            {
                "username": forbidden_user.username,
                "rol": WorkspaceMembership.Rol.ADMIN,
            },
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertFalse(
            WorkspaceMembership.objects.filter(
                workspace=self.workspace,
                usuario=forbidden_user,
            ).exists()
        )

    def test_editors_and_viewers_cannot_add_members(self):
        for user in (self.editor, self.viewer):
            with self.subTest(user=user.username):
                self.set_actor(user)
                candidate = self.create_user(f"candidate_{user.username}")
                response = self.client.post(
                    self.members_url,
                    {
                        "username": candidate.username,
                        "rol": WorkspaceMembership.Rol.VIEWER,
                    },
                    format="json",
                )
                self.assertEqual(
                    response.status_code,
                    status.HTTP_403_FORBIDDEN,
                )
                self.assertFalse(
                    WorkspaceMembership.objects.filter(
                        workspace=self.workspace,
                        usuario=candidate,
                    ).exists()
                )


    def test_adding_rejects_unknown_inactive_and_duplicate_users(self):
        self.set_actor(self.owner)
        inactive_user = self.create_user("inactive_member", is_active=False)
        cases = (
            ("missing_user", "no_such_user"),
            ("inactive_user", inactive_user.username),
            ("duplicate_user", self.editor.username),
        )

        for case, username in cases:
            with self.subTest(case=case):
                response = self.client.post(
                    self.members_url,
                    {
                        "username": username,
                        "rol": WorkspaceMembership.Rol.EDITOR,
                    },
                    format="json",
                )
                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )

        self.assertEqual(
            WorkspaceMembership.objects.filter(
                workspace=self.workspace,
            ).count(),
            5,
        )

    def test_owner_can_change_non_owner_role(self):
        self.set_actor(self.owner)
        response = self.client.patch(
            self.member_detail_url(self.editor_membership),
            {"rol": WorkspaceMembership.Rol.ADMIN},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.editor_membership.refresh_from_db()
        self.assertEqual(
            self.editor_membership.rol,
            WorkspaceMembership.Rol.ADMIN,
        )

    def test_admin_can_change_editor_and_demote_self(self):
        self.set_actor(self.admin)
        response = self.client.patch(
            self.member_detail_url(self.editor_membership),
            {"rol": WorkspaceMembership.Rol.VIEWER},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.editor_membership.refresh_from_db()
        self.assertEqual(
            self.editor_membership.rol,
            WorkspaceMembership.Rol.VIEWER,
        )

        response = self.client.patch(
            self.member_detail_url(self.admin_membership),
            {"rol": WorkspaceMembership.Rol.EDITOR},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.admin_membership.refresh_from_db()
        self.assertEqual(
            self.admin_membership.rol,
            WorkspaceMembership.Rol.EDITOR,
        )

    def test_admin_cannot_change_owner_or_another_admin_or_assign_admin(self):
        self.set_actor(self.admin)

        owner_response = self.client.patch(
            self.member_detail_url(self.owner_membership),
            {"rol": WorkspaceMembership.Rol.EDITOR},
            format="json",
        )
        other_admin_response = self.client.patch(
            self.member_detail_url(self.other_admin_membership),
            {"rol": WorkspaceMembership.Rol.EDITOR},
            format="json",
        )
        assign_admin_response = self.client.patch(
            self.member_detail_url(self.editor_membership),
            {"rol": WorkspaceMembership.Rol.ADMIN},
            format="json",
        )

        self.assertEqual(
            owner_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            other_admin_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            assign_admin_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.owner_membership.refresh_from_db()
        self.other_admin_membership.refresh_from_db()
        self.editor_membership.refresh_from_db()
        self.assertEqual(self.owner_membership.rol, WorkspaceMembership.Rol.OWNER)
        self.assertEqual(
            self.other_admin_membership.rol,
            WorkspaceMembership.Rol.ADMIN,
        )
        self.assertEqual(
            self.editor_membership.rol,
            WorkspaceMembership.Rol.EDITOR,
        )

    def test_editor_and_viewer_cannot_change_roles(self):
        for user in (self.editor, self.viewer):
            with self.subTest(user=user.username):
                self.set_actor(user)
                response = self.client.patch(
                    self.member_detail_url(self.viewer_membership),
                    {"rol": WorkspaceMembership.Rol.EDITOR},
                    format="json",
                )
                self.assertEqual(
                    response.status_code,
                    status.HTTP_403_FORBIDDEN,
                )
                delete_response = self.client.delete(
                    self.member_detail_url(self.viewer_membership),
                )
                self.assertEqual(
                    delete_response.status_code,
                    status.HTTP_403_FORBIDDEN,
                )
        self.viewer_membership.refresh_from_db()
        self.assertEqual(
            self.viewer_membership.rol,
            WorkspaceMembership.Rol.VIEWER,
        )

    def test_owner_cannot_change_owner_role_outside_transfer(self):
        self.set_actor(self.owner)
        response = self.client.patch(
            self.member_detail_url(self.owner_membership),
            {"rol": WorkspaceMembership.Rol.ADMIN},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.owner_membership.refresh_from_db()
        self.assertEqual(
            self.owner_membership.rol,
            WorkspaceMembership.Rol.OWNER,
        )

    def test_owner_can_remove_member_without_deleting_user(self):
        self.set_actor(self.owner)
        response = self.client.delete(
            self.member_detail_url(self.editor_membership),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertFalse(
            WorkspaceMembership.objects.filter(
                pk=self.editor_membership.pk,
            ).exists()
        )
        self.assertTrue(User.objects.filter(pk=self.editor.pk).exists())

    def test_admin_can_remove_editor_and_self_but_not_owner_or_other_admin(self):
        self.set_actor(self.admin)
        response = self.client.delete(
            self.member_detail_url(self.editor_membership),
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        owner_response = self.client.delete(
            self.member_detail_url(self.owner_membership),
        )
        other_admin_response = self.client.delete(
            self.member_detail_url(self.other_admin_membership),
        )
        self.assertEqual(
            owner_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            other_admin_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self_response = self.client.delete(
            self.member_detail_url(self.admin_membership),
        )
        self.assertEqual(
            self_response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())
        self.assertFalse(
            WorkspaceMembership.objects.filter(
                pk=self.admin_membership.pk,
            ).exists()
        )

    def test_owner_cannot_remove_owner_or_leave_workspace_ownerless(self):
        self.set_actor(self.owner)
        response = self.client.delete(
            self.member_detail_url(self.owner_membership),
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.owner_membership.refresh_from_db()
        self.workspace.refresh_from_db()
        self.assertEqual(
            self.owner_membership.rol,
            WorkspaceMembership.Rol.OWNER,
        )
        self.assertEqual(self.workspace.propietario_id, self.owner.pk)
        self.assertEqual(
            WorkspaceMembership.objects.filter(
                workspace=self.workspace,
                rol=WorkspaceMembership.Rol.OWNER,
            ).count(),
            1,
        )

    def test_only_owner_can_transfer_to_active_workspace_member(self):
        self.set_actor(self.admin)
        transfer_url = reverse(
            "workspace-transfer-ownership",
            kwargs={"workspace_id": self.workspace.pk},
        )
        response = self.client.post(
            transfer_url,
            {"username": self.editor.username},
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.workspace.refresh_from_db()
        self.assertEqual(self.workspace.propietario_id, self.owner.pk)

    def test_transfer_synchronizes_owner_and_demotes_previous_owner(self):
        self.set_actor(self.owner)
        transfer_url = reverse(
            "workspace-transfer-ownership",
            kwargs={"workspace_id": self.workspace.pk},
        )
        response = self.client.post(
            transfer_url,
            {"username": self.admin.username},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.workspace.refresh_from_db()
        self.owner_membership.refresh_from_db()
        self.admin_membership.refresh_from_db()

        self.assertEqual(self.workspace.propietario_id, self.admin.pk)
        self.assertEqual(
            self.owner_membership.rol,
            WorkspaceMembership.Rol.ADMIN,
        )
        self.assertEqual(
            self.admin_membership.rol,
            WorkspaceMembership.Rol.OWNER,
        )
        self.assertEqual(
            WorkspaceMembership.objects.filter(
                workspace=self.workspace,
                rol=WorkspaceMembership.Rol.OWNER,
            ).count(),
            1,
        )

    def test_transfer_rejects_nonmember_inactive_and_current_owner(self):
        self.set_actor(self.owner)
        transfer_url = reverse(
            "workspace-transfer-ownership",
            kwargs={"workspace_id": self.workspace.pk},
        )

        inactive_user = self.create_user("inactive_transfer", is_active=False)
        self.create_membership(
            inactive_user,
            WorkspaceMembership.Rol.EDITOR,
        )
        cases = (
            ("unknown", "unknown_transfer"),
            ("external", self.external_user.username),
            ("inactive", inactive_user.username),
            ("current_owner", self.owner.username),
        )

        for case, username in cases:
            with self.subTest(case=case):
                response = self.client.post(
                    transfer_url,
                    {"username": username},
                    format="json",
                )
                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )

        self.workspace.refresh_from_db()
        self.owner_membership.refresh_from_db()
        self.assertEqual(self.workspace.propietario_id, self.owner.pk)
        self.assertEqual(
            self.owner_membership.rol,
            WorkspaceMembership.Rol.OWNER,
        )

    def test_transfer_integrity_conflict_rolls_back_all_changes(self):
        self.set_actor(self.owner)
        transfer_url = reverse(
            "workspace-transfer-ownership",
            kwargs={"workspace_id": self.workspace.pk},
        )

        with patch.object(
            Workspace,
            "save",
            side_effect=IntegrityError("conflicto simulado"),
        ):
            response = self.client.post(
                transfer_url,
                {"username": self.admin.username},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.workspace.refresh_from_db()
        self.owner_membership.refresh_from_db()
        self.admin_membership.refresh_from_db()
        self.assertEqual(self.workspace.propietario_id, self.owner.pk)
        self.assertEqual(
            self.owner_membership.rol,
            WorkspaceMembership.Rol.OWNER,
        )
        self.assertEqual(
            self.admin_membership.rol,
            WorkspaceMembership.Rol.ADMIN,
        )
        self.assertEqual(
            WorkspaceMembership.objects.filter(
                workspace=self.workspace,
                rol=WorkspaceMembership.Rol.OWNER,
            ).count(),
            1,
        )

    def test_sqlite_lock_conflict_during_add_returns_conflict(self):
        self.set_actor(self.owner)
        candidate = self.create_user("sqlite_conflict_user")

        with patch.object(
            WorkspaceMembership.objects,
            "create",
            side_effect=OperationalError("database is locked"),
        ):
            response = self.client.post(
                self.members_url,
                {
                    "username": candidate.username,
                    "rol": WorkspaceMembership.Rol.EDITOR,
                },
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertFalse(
            WorkspaceMembership.objects.filter(
                workspace=self.workspace,
                usuario=candidate,
            ).exists()
        )


class WorkspaceAdminInvariantTests(APITestCase):

    def setUp(self):
        self.request = RequestFactory().get("/admin/")
        self.workspace_admin = WorkspaceAdmin(Workspace, admin.site)
        self.membership_admin = WorkspaceMembershipAdmin(
            WorkspaceMembership,
            admin.site,
        )
        self.owner = User.objects.create_user(
            username="admin_workspace_owner",
            password="PruebaSegura123!",
        )

    def test_admin_workspace_creation_creates_owner_membership(self):
        workspace = Workspace(
            nombre="Workspace creado desde admin",
            propietario=self.owner,
        )

        self.workspace_admin.save_model(
            self.request,
            workspace,
            form=None,
            change=False,
        )

        self.assertTrue(
            WorkspaceMembership.objects.filter(
                workspace=workspace,
                usuario=self.owner,
                rol=WorkspaceMembership.Rol.OWNER,
            ).exists()
        )

    def test_admin_cannot_change_existing_workspace_owner(self):
        workspace = Workspace.objects.create(
            nombre="Workspace existente",
            propietario=self.owner,
        )

        self.assertIn(
            "propietario",
            self.workspace_admin.get_readonly_fields(
                self.request,
                workspace,
            ),
        )

    def test_admin_membership_changes_are_disabled(self):
        self.assertFalse(
            self.membership_admin.has_add_permission(self.request)
        )
        self.assertFalse(
            self.membership_admin.has_delete_permission(self.request)
        )
        self.assertEqual(
            set(self.membership_admin.readonly_fields),
            {"workspace", "usuario", "rol", "fecha_creacion"},
        )

    def test_admin_workspace_owner_field_only_lists_active_users(self):
        inactive_user = User.objects.create_user(
            username="inactive_admin_owner",
            password="PruebaSegura123!",
            is_active=False,
        )
        field = self.workspace_admin.formfield_for_foreignkey(
            Workspace._meta.get_field("propietario"),
            self.request,
        )

        self.assertIn(self.owner, field.queryset)
        self.assertNotIn(inactive_user, field.queryset)

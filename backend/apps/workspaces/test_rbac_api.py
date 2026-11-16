from rest_framework import status
from rest_framework.test import APITestCase

from apps.workspaces.models import WorkspaceMembership
from apps.workspaces.test_utils import crear_workspace_prueba
from apps.workspaces.test_utils import crear_problema_prueba


class WorkspaceRBACAPITests(APITestCase):

    def setUp(self):
        self.user, self.workspace = crear_workspace_prueba()

        self.membership = WorkspaceMembership.objects.get(
            workspace=self.workspace,
            usuario=self.user,
        )

        self.client.force_authenticate(user=self.user)
        self.client.credentials(
            HTTP_X_WORKSPACE_ID=str(self.workspace.pk)
        )

    def cambiar_rol(self, rol):
        self.membership.rol = rol
        self.membership.save(update_fields=["rol"])

    def test_viewer_puede_consultar_problemas(self):
        self.cambiar_rol(WorkspaceMembership.Rol.VIEWER)

        response = self.client.get("/api/problemas/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_viewer_no_puede_escribir_en_endpoints(self):
        self.cambiar_rol(WorkspaceMembership.Rol.VIEWER)

        endpoints = [
            "/api/problemas/",
            "/api/productos/",
            "/api/recursos/",
            "/api/consumos/",
            "/api/ejecuciones/",
            "/api/resultados-productos/",
            "/api/resultados-recursos/",
            "/api/problemas/999999/ejecutar/",
            "/api/analisis-ia/ejecuciones/999999/generar/",
        ]

        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.post(
                    endpoint,
                    {},
                    format="json",
                )

                self.assertEqual(
                    response.status_code,
                    status.HTTP_403_FORBIDDEN,
                    msg=f"VIEWER pudo escribir en {endpoint}",
                )

    def test_viewer_no_puede_modificar_ni_eliminar_problemas(self):
        problema = crear_problema_prueba(
            self.workspace,
            nombre="Problema protegido",
        )

        self.cambiar_rol(WorkspaceMembership.Rol.VIEWER)

        url = f"/api/problemas/{problema.pk}/"

        response_patch = self.client.patch(
            url,
            {"nombre": "Nombre modificado"},
            format="json",
        )

        self.assertEqual(
            response_patch.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        response_delete = self.client.delete(url)

        self.assertEqual(
            response_delete.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_owner_admin_y_editor_pueden_crear_problemas(self):
        roles = [
            WorkspaceMembership.Rol.OWNER,
            WorkspaceMembership.Rol.ADMIN,
            WorkspaceMembership.Rol.EDITOR,
        ]

        for rol in roles:
            with self.subTest(rol=rol):
                self.cambiar_rol(rol)

                response = self.client.post(
                    "/api/problemas/",
                    {"nombre": f"Problema {rol}"},
                    format="json",
                )

                self.assertEqual(
                    response.status_code,
                    status.HTTP_201_CREATED,
                    msg=f"El rol {rol} no pudo crear un problema: "
                        f"{response.data}",
                )

from django.db import IntegrityError, OperationalError, connection, transaction
from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Workspace, WorkspaceMembership
from .serializers import (
    WorkspaceMemberCreateSerializer,
    WorkspaceMemberRoleSerializer,
    WorkspaceMemberSerializer,
    WorkspaceMembershipSerializer,
    WorkspaceOwnershipTransferSerializer,
)


class WorkspaceMemberAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def is_sqlite_lock_conflict(error):
        message = str(error).casefold()
        return connection.vendor == "sqlite" and (
            "locked" in message or "busy" in message
        )

    def get_actor_membership(self, request, workspace_id):
        membership = WorkspaceMembership.objects.select_related(
            "workspace"
        ).filter(
            workspace_id=workspace_id,
            usuario=request.user,
        ).first()

        if membership is None:
            raise NotFound(
                "Workspace inexistente o sin acceso para este usuario."
            )

        return membership

    def get_locked_actor_membership(self, request, workspace_id):
        workspace = Workspace.objects.select_for_update().filter(
            pk=workspace_id,
        ).first()
        if workspace is None:
            raise NotFound(
                "Workspace inexistente o sin acceso para este usuario."
            )

        membership = WorkspaceMembership.objects.select_related(
            "workspace"
        ).filter(
            workspace=workspace,
            usuario=request.user,
        ).first()
        if membership is None:
            raise NotFound(
                "Workspace inexistente o sin acceso para este usuario."
            )
        return membership

    def get_target_membership(self, workspace_id, membership_id):
        membership = WorkspaceMembership.objects.select_related(
            "workspace",
            "usuario",
        ).filter(
            workspace_id=workspace_id,
            pk=membership_id,
        ).first()

        if membership is None:
            raise NotFound("La membresía no existe en este Workspace.")

        return membership

    def require_role(self, membership, allowed_roles):
        if membership.rol not in allowed_roles:
            raise PermissionDenied(
                "Tu rol no permite administrar miembros de este Workspace."
            )


class WorkspaceMemberListCreateAPIView(WorkspaceMemberAPIView):

    @extend_schema(
        tags=["Miembros"],
        responses={200: WorkspaceMemberSerializer(many=True)},
    )
    def get(self, request, workspace_id):
        actor_membership = self.get_actor_membership(
            request,
            workspace_id,
        )
        memberships = WorkspaceMembership.objects.filter(
            workspace=actor_membership.workspace,
        ).select_related(
            "usuario",
        ).order_by(
            "usuario__username",
        )

        return Response(
            WorkspaceMemberSerializer(memberships, many=True).data,
        )

    @extend_schema(
        tags=["Miembros"],
        request=WorkspaceMemberCreateSerializer,
        responses={
            201: WorkspaceMemberSerializer,
            400: OpenApiResponse(description="Usuario o rol inválido."),
            403: OpenApiResponse(description="Rol insuficiente."),
            409: OpenApiResponse(description="La membresía ya existe."),
        },
    )
    def post(self, request, workspace_id):
        try:
            with transaction.atomic():
                actor_membership = self.get_locked_actor_membership(
                    request,
                    workspace_id,
                )
                self.require_role(
                    actor_membership,
                    {
                        WorkspaceMembership.Rol.OWNER,
                        WorkspaceMembership.Rol.ADMIN,
                    },
                )

                serializer = WorkspaceMemberCreateSerializer(
                    data=request.data,
                    context={
                        "workspace": actor_membership.workspace,
                        "actor_role": actor_membership.rol,
                    },
                )
                serializer.is_valid(raise_exception=True)

                usuario = get_user_model().objects.filter(
                    pk=serializer.validated_data["usuario"].pk,
                    is_active=True,
                ).first()
                if usuario is None:
                    return Response(
                        {"username": "El usuario debe existir y estar activo."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                membership = WorkspaceMembership.objects.create(
                    workspace=actor_membership.workspace,
                    usuario=usuario,
                    rol=serializer.validated_data["rol"],
                )
        except IntegrityError:
            return Response(
                {
                    "detail": (
                        "No se pudo agregar el usuario; "
                        "puede que ya pertenezca a este Workspace."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )
        except OperationalError as error:
            if not self.is_sqlite_lock_conflict(error):
                raise

            return Response(
                {
                    "detail": (
                        "El Workspace está siendo modificado. "
                        "Reintenta agregar el usuario."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            WorkspaceMemberSerializer(membership).data,
            status=status.HTTP_201_CREATED,
        )


class WorkspaceMemberDetailAPIView(WorkspaceMemberAPIView):

    @extend_schema(
        tags=["Miembros"],
        request=WorkspaceMemberRoleSerializer,
        responses={
            200: WorkspaceMemberSerializer,
            403: OpenApiResponse(description="Rol insuficiente."),
            404: OpenApiResponse(description="Membresía no encontrada."),
            409: OpenApiResponse(description="Conflicto de integridad."),
        },
    )
    def patch(self, request, workspace_id, membership_id):
        try:
            with transaction.atomic():
                actor_membership = self.get_locked_actor_membership(
                    request,
                    workspace_id,
                )
                self.require_role(
                    actor_membership,
                    {
                        WorkspaceMembership.Rol.OWNER,
                        WorkspaceMembership.Rol.ADMIN,
                    },
                )
                target_membership = self.get_target_membership(
                    workspace_id,
                    membership_id,
                )

                if (
                    target_membership.rol == WorkspaceMembership.Rol.OWNER
                    or target_membership.usuario_id
                    == actor_membership.workspace.propietario_id
                ):
                    raise PermissionDenied(
                        "La propiedad solo puede cambiarse mediante "
                        "transferencia."
                    )

                if (
                    actor_membership.rol == WorkspaceMembership.Rol.ADMIN
                    and target_membership.rol
                    == WorkspaceMembership.Rol.ADMIN
                    and target_membership.usuario_id != request.user.pk
                ):
                    raise PermissionDenied(
                        "Un ADMIN no puede modificar a otro ADMIN."
                    )

                serializer = WorkspaceMemberRoleSerializer(
                    target_membership,
                    data=request.data,
                    context={
                        "actor_role": actor_membership.rol,
                        "actor_user_id": request.user.pk,
                    },
                )
                serializer.is_valid(raise_exception=True)

                target_membership.rol = serializer.validated_data["rol"]
                target_membership.save(update_fields=["rol"])
        except IntegrityError:
            return Response(
                {"detail": "El cambio entró en conflicto con el estado actual."},
                status=status.HTTP_409_CONFLICT,
            )
        except OperationalError as error:
            if not self.is_sqlite_lock_conflict(error):
                raise

            return Response(
                {
                    "detail": (
                        "El Workspace está siendo modificado. "
                        "Reintenta el cambio de rol."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(WorkspaceMemberSerializer(target_membership).data)

    @extend_schema(
        tags=["Miembros"],
        responses={
            204: OpenApiResponse(description="Membresía eliminada."),
            403: OpenApiResponse(description="Rol insuficiente."),
            404: OpenApiResponse(description="Membresía no encontrada."),
            409: OpenApiResponse(description="Conflicto de integridad."),
        },
    )
    def delete(self, request, workspace_id, membership_id):
        try:
            with transaction.atomic():
                actor_membership = self.get_locked_actor_membership(
                    request,
                    workspace_id,
                )
                self.require_role(
                    actor_membership,
                    {
                        WorkspaceMembership.Rol.OWNER,
                        WorkspaceMembership.Rol.ADMIN,
                    },
                )
                target_membership = self.get_target_membership(
                    workspace_id,
                    membership_id,
                )

                if (
                    target_membership.rol == WorkspaceMembership.Rol.OWNER
                    or target_membership.usuario_id
                    == actor_membership.workspace.propietario_id
                ):
                    raise PermissionDenied(
                        "No se puede retirar al propietario del Workspace."
                    )

                if (
                    actor_membership.rol == WorkspaceMembership.Rol.ADMIN
                    and target_membership.rol
                    == WorkspaceMembership.Rol.ADMIN
                    and target_membership.usuario_id != request.user.pk
                ):
                    raise PermissionDenied(
                        "Un ADMIN no puede retirar a otro ADMIN."
                    )

                target_membership.delete()
        except IntegrityError:
            return Response(
                {"detail": "La operación entró en conflicto con el estado actual."},
                status=status.HTTP_409_CONFLICT,
            )
        except OperationalError as error:
            if not self.is_sqlite_lock_conflict(error):
                raise

            return Response(
                {
                    "detail": (
                        "El Workspace está siendo modificado. "
                        "Reintenta retirar al miembro."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkspaceOwnershipTransferAPIView(WorkspaceMemberAPIView):

    @extend_schema(
        tags=["Miembros"],
        request=WorkspaceOwnershipTransferSerializer,
        responses={
            200: WorkspaceMemberSerializer,
            400: OpenApiResponse(description="Destinatario inválido."),
            403: OpenApiResponse(description="Solo OWNER puede transferir."),
            409: OpenApiResponse(description="Conflicto de integridad."),
        },
    )
    def post(self, request, workspace_id):
        try:
            with transaction.atomic():
                actor_membership = self.get_locked_actor_membership(
                    request,
                    workspace_id,
                )
                self.require_role(
                    actor_membership,
                    {WorkspaceMembership.Rol.OWNER},
                )

                serializer = WorkspaceOwnershipTransferSerializer(
                    data=request.data,
                    context={"workspace": actor_membership.workspace},
                )
                serializer.is_valid(raise_exception=True)
                requested_membership = serializer.validated_data["membresia"]

                if actor_membership.rol != WorkspaceMembership.Rol.OWNER:
                    raise PermissionDenied(
                        "Solo un OWNER puede transferir la propiedad."
                    )

                workspace = actor_membership.workspace
                target_membership = WorkspaceMembership.objects.select_related(
                    "usuario"
                ).get(
                    pk=requested_membership.pk,
                    workspace=workspace,
                )
                if not target_membership.usuario.is_active:
                    return Response(
                        {"username": "El usuario debe estar activo."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                WorkspaceMembership.objects.filter(
                    workspace=workspace,
                ).exclude(
                    pk=target_membership.pk,
                ).filter(
                    rol=WorkspaceMembership.Rol.OWNER,
                ).update(
                    rol=WorkspaceMembership.Rol.ADMIN,
                )

                WorkspaceMembership.objects.filter(
                    workspace=workspace,
                    usuario_id=workspace.propietario_id,
                ).exclude(
                    pk=target_membership.pk,
                ).update(
                    rol=WorkspaceMembership.Rol.ADMIN,
                )

                workspace.propietario_id = target_membership.usuario_id
                workspace.save(update_fields=["propietario"])

                target_membership.rol = WorkspaceMembership.Rol.OWNER
                target_membership.save(update_fields=["rol"])
        except WorkspaceMembership.DoesNotExist:
            raise NotFound(
                "La membresía o el Workspace ya no están disponibles."
            )
        except IntegrityError:
            return Response(
                {
                    "detail": (
                        "La transferencia entró en conflicto con "
                        "el estado actual del Workspace."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )
        except OperationalError as error:
            if not self.is_sqlite_lock_conflict(error):
                raise

            return Response(
                {
                    "detail": (
                        "El Workspace está siendo modificado. "
                        "Reintenta la transferencia."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(WorkspaceMemberSerializer(target_membership).data)


class WorkspaceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Lista únicamente los Workspaces a los que pertenece el usuario.
    No permite crear, modificar ni eliminar Workspaces desde este endpoint.
    """

    serializer_class = WorkspaceMembershipSerializer
    queryset = WorkspaceMembership.objects.none()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WorkspaceMembership.objects.filter(
            usuario=self.request.user
        ).select_related("workspace").order_by("workspace__nombre")

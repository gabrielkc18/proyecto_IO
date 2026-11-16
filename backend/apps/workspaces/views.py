from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import WorkspaceMembership
from .serializers import WorkspaceMembershipSerializer


class WorkspaceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Lista únicamente los Workspaces a los que pertenece el usuario.
    No permite crear, modificar ni eliminar Workspaces desde este endpoint.
    """

    serializer_class = WorkspaceMembershipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WorkspaceMembership.objects.filter(
            usuario=self.request.user
        ).select_related("workspace").order_by("workspace__nombre")

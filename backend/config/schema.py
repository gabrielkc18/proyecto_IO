from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import OpenApiParameter

from apps.workspaces.mixins import WorkspaceContextMixin


class PlanificaIOSchema(AutoSchema):
    def get_override_parameters(self):
        parameters = super().get_override_parameters()
        if isinstance(self.view, WorkspaceContextMixin):
            parameters.append(
                OpenApiParameter(
                    name="X-Workspace-ID",
                    type=int,
                    location=OpenApiParameter.HEADER,
                    required=True,
                    description=(
                        "Workspace activo al que pertenece el usuario "
                        "autenticado."
                    ),
                )
            )
        return parameters

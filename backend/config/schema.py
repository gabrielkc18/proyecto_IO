from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import OpenApiParameter


class PlanificaIOSchema(AutoSchema):
    def get_override_parameters(self):
        parameters = super().get_override_parameters()
        workspace_header = getattr(self.view, "workspace_header", None)
        if workspace_header is not None:
            parameters.append(
                OpenApiParameter(
                    name=workspace_header,
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

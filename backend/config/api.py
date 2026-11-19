from sqlite3 import SQLITE_CONSTRAINT_UNIQUE

from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.filters import BaseFilterBackend


MAX_ID = 2**63 - 1


def identificador_positivo(value, field):
    try:
        identifier = int(value)
    except (TypeError, ValueError):
        identifier = 0
    if not 1 <= identifier <= MAX_ID:
        raise ValidationError({field: "Debe ser un identificador entero positivo válido."})
    return identifier


class PlanningIdFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        for parameter, fields in view.id_filters.items():
            if parameter in request.query_params:
                identifier = identificador_positivo(request.query_params[parameter], parameter)
                queryset = queryset.filter(**dict.fromkeys(fields, identifier))
        return queryset

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": name,
                "in": "query",
                "required": False,
                "schema": {"type": "integer", "minimum": 1, "maximum": MAX_ID},
                "description": "Identificador dentro del workspace activo.",
            }
            for name in view.id_filters
        ]


class PlanningConflict(APIException):
    status_code = 409
    default_code = "conflict"


class PlanningWriteMixin:
    uniqueness_constraints = {
        "unique_problema_por_workspace",
        "unique_producto_por_problema",
        "unique_recurso_por_problema",
        "unique_consumo_producto_recurso",
    }

    def _write(self, operation, *args, **kwargs):
        try:
            with transaction.atomic():
                return operation(*args, **kwargs)
        except IntegrityError as error:
            cause = error.__cause__
            constraint = getattr(getattr(cause, "diag", None), "constraint_name", None)
            if (
                constraint in self.uniqueness_constraints
                or getattr(cause, "sqlite_errorcode", None) == SQLITE_CONSTRAINT_UNIQUE
            ):
                raise PlanningConflict("Ya existe un registro con esos datos.") from error
            raise

    def create(self, *args, **kwargs):
        return self._write(super().create, *args, **kwargs)

    def update(self, *args, **kwargs):
        return self._write(super().update, *args, **kwargs)

    @extend_schema(responses={
        204: None,
        404: OpenApiResponse(description="Registro inexistente o fuera del workspace."),
        409: OpenApiResponse(description="El registro tiene historial asociado."),
    })
    def destroy(self, *args, **kwargs):
        try:
            return super().destroy(*args, **kwargs)
        except ProtectedError as error:
            raise PlanningConflict(
                "El registro tiene historial asociado y no se puede eliminar."
            ) from error

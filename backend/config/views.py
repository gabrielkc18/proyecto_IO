import logging

from django.db import DatabaseError, connection
from django.http import JsonResponse
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny


logger = logging.getLogger(__name__)


@extend_schema(
    tags=["Health"],
    auth=[],
    responses={
        200: inline_serializer(
            name="HealthCheckResponse",
            fields={"status": serializers.CharField()},
        ),
        503: inline_serializer(
            name="HealthCheckUnavailableResponse",
            fields={"status": serializers.CharField()},
        ),
    },
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def health_check(_request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError as error:
        logger.error(
            "Health check database query failed (%s)",
            type(error).__name__,
        )
        return JsonResponse({"status": "unavailable"}, status=503)

    return JsonResponse({"status": "ok"})

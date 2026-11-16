
from rest_framework import viewsets

from .models import AnalisisIA
from .serializers import AnalisisIASerializer

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import GenerarAnalisisSerializer
from .services.analisis import generar_analisis
from .services.proveedor_ia import ErrorProveedorIA


class AnalisisIAViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = AnalisisIASerializer

    queryset = AnalisisIA.objects.select_related(
        "ejecucion",
        "ejecucion__problema"
    ).all()

    def get_queryset(self):
        queryset = super().get_queryset()

        ejecucion_id = self.request.query_params.get("ejecucion")
        problema_id = self.request.query_params.get("problema")

        if ejecucion_id:
            queryset = queryset.filter(
                ejecucion_id=ejecucion_id
            )

        if problema_id:
            queryset = queryset.filter(
                ejecucion__problema_id=problema_id
            )

        return queryset

class GenerarAnalisisAPIView(APIView):

    def post(self, request, ejecucion_id):

        serializer = GenerarAnalisisSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        pregunta = serializer.validated_data.get(
            "pregunta",
            "",
        )

        try:
            analisis = generar_analisis(
                ejecucion_id=ejecucion_id,
                pregunta=pregunta,
            )

        except ValueError as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except ErrorProveedorIA as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            AnalisisIASerializer(analisis).data,
            status=status.HTTP_201_CREATED,
        )
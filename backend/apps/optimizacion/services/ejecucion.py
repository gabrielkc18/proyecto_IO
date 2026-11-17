
from decimal import Decimal, ROUND_HALF_UP
import logging

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.problemas.models import Problema
from apps.productos.models import Producto
from apps.recursos.models import Recurso, ConsumoRecurso
from apps.optimizacion.models import Ejecucion
from apps.resultados.models import ResultadoProducto, ResultadoRecurso

from apps.optimizacion.services.solver import resolver_problema


logger = logging.getLogger(__name__)


def a_decimal(valor):
    """Convierte un valor numérico a Decimal con dos decimales."""
    return Decimal(str(valor)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


def ejecutar_optimizacion(problema_id):
    """
    Ejecuta la optimización de un problema y persiste sus resultados.
    """

    # 1. Consultar y validar el problema
    problema = Problema.objects.get(pk=problema_id)

    if problema.estado != Problema.Estado.LISTO:
        raise ValueError(
            "El problema debe estar en estado LISTO para optimizarse."
        )

    productos_db = list(
        Producto.objects.filter(
            problema=problema,
            activo=True
        ).order_by("codigo")
    )

    recursos_db = list(
        Recurso.objects.filter(
            problema=problema,
            activo=True
        ).order_by("nombre")
    )

    if not productos_db:
        raise ValueError("El problema no tiene productos activos.")

    if not recursos_db:
        raise ValueError("El problema no tiene recursos activos.")

    if len(productos_db) > settings.OPTIMIZATION_MAX_PRODUCTS:
        raise ValueError(
            "El problema supera el límite de productos por ejecución."
        )
    if len(recursos_db) > settings.OPTIMIZATION_MAX_RESOURCES:
        raise ValueError(
            "El problema supera el límite de recursos por ejecución."
        )

    # 2. Consultar consumos asociados al problema
    consumos_db = list(
        ConsumoRecurso.objects.filter(
            producto__problema=problema,
            recurso__problema=problema,
            producto__activo=True,
            recurso__activo=True,
        ).select_related("producto", "recurso")
    )

    # 3. Construir la estructura de consumos
    consumos_por_recurso = {
        recurso.id: {}
        for recurso in recursos_db
    }
    consumos_para_snapshot = {
        recurso.id: {}
        for recurso in recursos_db
    }

    for consumo in consumos_db:
        consumos_por_recurso[consumo.recurso_id][
            consumo.producto.codigo
        ] = float(consumo.cantidad_por_unidad)
        consumos_para_snapshot[consumo.recurso_id][
            consumo.producto.codigo
        ] = str(consumo.cantidad_por_unidad)

    # 4. Preparar los datos para PuLP
    productos_solver = [
        {
            "codigo": producto.codigo,
            "utilidad_unitaria": float(producto.utilidad_unitaria)
        }
        for producto in productos_db
    ]

    recursos_solver = [
        {
            "nombre": recurso.nombre,
            "disponibilidad": float(recurso.disponibilidad),
            "consumos": consumos_por_recurso[recurso.id]
        }
        for recurso in recursos_db
    ]

    sentido = (
        "MAX"
        if problema.sentido_objetivo == Problema.SentidoObjetivo.MAXIMIZAR
        else "MIN"
    )

    # 5. Construir snapshot histórico de entrada
    snapshot = {
        "problema_id": problema.id,
        "nombre_problema": problema.nombre,
        "sentido_objetivo": problema.sentido_objetivo,
        "productos": [
            {
                "codigo": producto.codigo,
                "nombre": producto.nombre,
                "utilidad_unitaria": str(producto.utilidad_unitaria)
            }
            for producto in productos_db
        ],
        "recursos": [
            {
                "nombre": recurso.nombre,
                "unidad_medida": recurso.unidad_medida,
                "disponibilidad": str(recurso.disponibilidad),
                "consumos": consumos_para_snapshot[recurso.id],
            }
            for recurso in recursos_db
        ]
    }

    # 6. Crear registro de ejecución
    ejecucion = Ejecucion.objects.create(
        problema=problema,
        estado_proceso=Ejecucion.EstadoProceso.EN_CURSO,
        solver_nombre="CBC",
        snapshot_entrada=snapshot
    )

    try:
        # 7. Resolver el modelo matemático
        resultado = resolver_problema(
            productos_solver,
            recursos_solver,
            sentido,
            time_limit=settings.OPTIMIZATION_TIME_LIMIT_SECONDS,
        )

        estado_solver = resultado["estado"]

        estados_validos = {
            "Optimal": Ejecucion.EstadoSolver.OPTIMAL,
            "Infeasible": Ejecucion.EstadoSolver.INFEASIBLE,
            "Unbounded": Ejecucion.EstadoSolver.UNBOUNDED,
            "Not Solved": Ejecucion.EstadoSolver.NOT_SOLVED,
            "Undefined": Ejecucion.EstadoSolver.UNDEFINED,
        }

        if estado_solver not in estados_validos:
            raise ValueError(
                f"Estado del solver no reconocido: {estado_solver}"
            )

        # 8. Guardar resultados de forma atómica
        with transaction.atomic():

            if estado_solver == "Optimal":

                ejecucion.utilidad_total = a_decimal(
                    resultado["utilidad_total"]
                )

                productos_por_codigo = {
                    producto.codigo: producto
                    for producto in productos_db
                }

                for item in resultado["productos"]:
                    producto = productos_por_codigo[item["codigo"]]

                    ResultadoProducto.objects.create(
                        ejecucion=ejecucion,
                        producto=producto,
                        nombre_producto=producto.nombre,
                        utilidad_unitaria=producto.utilidad_unitaria,
                        cantidad=item["cantidad"],
                        utilidad_aportada=a_decimal(
                            item["utilidad_aportada"]
                        )
                    )

                recursos_por_nombre = {
                    recurso.nombre: recurso
                    for recurso in recursos_db
                }

                for item in resultado["recursos"]:
                    recurso = recursos_por_nombre[item["nombre"]]

                    ResultadoRecurso.objects.create(
                        ejecucion=ejecucion,
                        recurso=recurso,
                        nombre_recurso=recurso.nombre,
                        unidad_medida=recurso.unidad_medida,
                        disponibilidad=recurso.disponibilidad,
                        consumo_total=a_decimal(
                            item["consumo_total"]
                        ),
                        holgura=a_decimal(item["holgura"]),
                        estado_uso=item["estado_uso"]
                    )

            ejecucion.estado_solver = estados_validos[estado_solver]
            ejecucion.estado_proceso = (
                Ejecucion.EstadoProceso.TERMINADO
            )
            ejecucion.fecha_fin = timezone.now()
            ejecucion.save()

    except Exception:
        logger.exception(
            "Falló una ejecución de optimización "
            "execution_id=%s problem_id=%s",
            ejecucion.pk,
            problema.pk,
        )
        ejecucion.estado_proceso = Ejecucion.EstadoProceso.ERROR
        ejecucion.mensaje_error = (
            "La ejecución no pudo completarse. Contacta al soporte."
        )
        ejecucion.fecha_fin = timezone.now()
        ejecucion.save(
            update_fields=[
                "estado_proceso",
                "mensaje_error",
                "fecha_fin"
            ]
        )

    return ejecucion

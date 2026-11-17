from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.inteligencia_artificial.models import SolicitudAnalisisIA


class Command(BaseCommand):
    help = "Marca como fallidas solicitudes IA PROCESSING que superen una antigüedad."

    def add_arguments(self, parser):
        parser.add_argument("--older-than-minutes", type=int, required=True)
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo informa cuántas solicitudes coinciden.",
        )

    def handle(self, *args, **options):
        age_minutes = options["older_than_minutes"]
        if age_minutes <= 0:
            raise CommandError("--older-than-minutes debe ser mayor que cero.")

        cutoff = timezone.now() - timedelta(minutes=age_minutes)
        stale_requests = SolicitudAnalisisIA.objects.filter(
            estado=SolicitudAnalisisIA.Estado.PROCESSING,
            fecha_creacion__lt=cutoff,
        )

        if options["dry_run"]:
            self.stdout.write(
                f"Solicitudes PROCESSING que cumplen el umbral: "
                f"{stale_requests.count()}."
            )
            return

        recovered = 0
        for request_id in stale_requests.values_list("pk", flat=True).iterator():
            with transaction.atomic():
                request = (
                    SolicitudAnalisisIA.objects.select_for_update()
                    .filter(
                        pk=request_id,
                        estado=SolicitudAnalisisIA.Estado.PROCESSING,
                        fecha_creacion__lt=cutoff,
                    )
                    .first()
                )
                if request is None:
                    continue
                request.estado = SolicitudAnalisisIA.Estado.FAILED
                request.save(update_fields=["estado", "fecha_actualizacion"])
                recovered += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Solicitudes antiguas marcadas como FAILED: {recovered}."
            )
        )

"""Funciones para pasar fechas de UTC a la hora de Colombia."""

from datetime import datetime, timedelta, timezone

# Colombia esta en UTC-5 todo el anio (no tiene horario de verano),
# por eso basta con una zona fija de -5 horas.
ZONA_COLOMBIA = timezone(timedelta(hours=-5), name="America/Bogota")

FORMATO_LEGIBLE = "%Y-%m-%d %H:%M:%S"


def a_hora_colombia(fecha: datetime | None) -> str | None:
    """Convierte una fecha UTC a texto en hora de Colombia.

    Ejemplo: 2026-10-10 19:43:15+00:00  ->  "2026-10-10 14:43:15 (UTC-05:00)"
    """
    if fecha is None:
        return None
    if fecha.tzinfo is None:
        # Si llega sin zona horaria se asume que esta en UTC
        fecha = fecha.replace(tzinfo=timezone.utc)
    local = fecha.astimezone(ZONA_COLOMBIA)
    return local.strftime(FORMATO_LEGIBLE) + " (UTC-05:00)"


def a_utc(fecha: datetime) -> datetime:
    """Pasa una fecha de un filtro (desde / hasta) a UTC.

    Si el usuario escribe la fecha sin zona horaria (ej: 2026-10-10T14:00:00)
    se entiende que esta en hora de Colombia, porque asi la ve en las respuestas.
    """
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=ZONA_COLOMBIA)
    return fecha.astimezone(timezone.utc)

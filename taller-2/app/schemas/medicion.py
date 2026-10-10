"""Esquemas Pydantic de las mediciones.

Aqui hay dos grupos de esquemas:
1. Los que validan el mensaje que llega por MQTT (MensajeSensor y Medida).
2. El que se usa para responder en los endpoints GET (MedicionRespuesta).
"""

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.fechas import a_hora_colombia


# ---------------------------------------------------------------------------
# 1. Validacion del payload MQTT
# ---------------------------------------------------------------------------

class Medida(BaseModel):
    """Una magnitud dentro de "measurements". Ej: {"value": 24.6, "unit": "C"}"""

    # extra="forbid": si llegan campos que no esperamos, el mensaje se rechaza
    # strict=True: no se aceptan conversiones automaticas (ej: "24.6" como texto)
    model_config = ConfigDict(extra="forbid", strict=True)

    value: float = Field(allow_inf_nan=False)
    unit: str = Field(min_length=1)


class MensajeSensor(BaseModel):
    """Estructura completa del mensaje que publica el sensor."""

    model_config = ConfigDict(extra="forbid", strict=True)

    sensor_id: str = Field(min_length=1, max_length=20)
    timestamp: datetime
    measurements: dict[str, Medida] = Field(min_length=1)

    @field_validator("timestamp", mode="before")
    @classmethod
    def timestamp_debe_ser_texto_iso(cls, valor):
        """El timestamp debe venir como texto ISO 8601, ej: 2026-10-07T16:25:30Z"""
        if not isinstance(valor, str):
            raise ValueError("el timestamp debe ser un texto en formato ISO 8601")
        try:
            # fromisoformat entiende la "Z" final desde Python 3.11
            return datetime.fromisoformat(valor)
        except ValueError:
            raise ValueError(f"'{valor}' no es una fecha ISO 8601 valida")

    @field_validator("timestamp")
    @classmethod
    def timestamp_debe_estar_en_utc(cls, valor: datetime):
        """El docente indico que el timestamp viene en UTC, se exige que lo diga."""
        if valor.tzinfo is None or valor.utcoffset().total_seconds() != 0:
            raise ValueError("el timestamp debe estar en UTC (terminar en 'Z' o '+00:00')")
        return valor.astimezone(timezone.utc)


# ---------------------------------------------------------------------------
# 2. Respuesta de los endpoints
# ---------------------------------------------------------------------------

class MedicionRespuesta(BaseModel):
    id: int
    sensor_magnitud_id: int
    magnitud: str
    unidad: str
    valor: float
    timestamp_utc: str
    timestamp_colombia: str
    fecha_recepcion_colombia: str


def convertir_medicion(medicion) -> MedicionRespuesta:
    """Convierte un objeto ORM Medicion en la respuesta que ve el usuario."""
    return MedicionRespuesta(
        id=medicion.id,
        sensor_magnitud_id=medicion.sensor_magnitud_id,
        magnitud=medicion.sensor_magnitud.magnitud,
        unidad=medicion.sensor_magnitud.unidad,
        valor=float(medicion.valor),
        timestamp_utc=medicion.timestamp_utc.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        timestamp_colombia=a_hora_colombia(medicion.timestamp_utc),
        fecha_recepcion_colombia=a_hora_colombia(medicion.fecha_recepcion),
    )

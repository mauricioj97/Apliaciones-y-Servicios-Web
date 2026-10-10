"""Esquemas Pydantic para responder datos de la tabla sensor_magnitudes."""

from pydantic import BaseModel, ConfigDict


class SensorMagnitudRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sensor_id: int
    magnitud: str
    unidad: str
    # En la base son NUMERIC; se devuelven como numero decimal normal
    valor_minimo: float
    valor_maximo: float

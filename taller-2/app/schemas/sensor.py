"""Esquemas Pydantic para responder datos de la tabla sensores."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer

from app.utils.fechas import a_hora_colombia


class SensorRespuesta(BaseModel):
    # from_attributes permite crear el esquema directamente desde el objeto ORM
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nombre: str
    categoria: str
    ubicacion: str
    activo: bool
    fecha_registro: datetime

    @field_serializer("fecha_registro")
    def mostrar_en_hora_colombia(self, fecha: datetime) -> str:
        return a_hora_colombia(fecha)

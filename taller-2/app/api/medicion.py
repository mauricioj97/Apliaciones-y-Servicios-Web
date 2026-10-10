"""Endpoints de consulta de mediciones."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.crud import medicion as crud_medicion
from app.crud import sensor as crud_sensor
from app.crud import sensor_magnitud as crud_magnitud
from app.database.connection import get_db
from app.schemas.medicion import MedicionRespuesta, convertir_medicion
from app.utils.fechas import a_utc

router = APIRouter(tags=["Mediciones"])


def verificar_sensor(db: Session, sensor_id: int):
    """Si el sensor no existe responde 404."""
    sensor = crud_sensor.obtener_sensor(db, sensor_id)
    if sensor is None:
        raise HTTPException(status_code=404, detail=f"No existe un sensor con id {sensor_id}")
    return sensor


@router.get("/mediciones/{medicion_id}", response_model=MedicionRespuesta)
def obtener_medicion(
    medicion_id: int = Path(gt=0),
    db: Session = Depends(get_db),
):
    """Consulta una medicion por su id."""
    medicion = crud_medicion.obtener_medicion(db, medicion_id)
    if medicion is None:
        raise HTTPException(status_code=404, detail=f"No existe una medicion con id {medicion_id}")
    return convertir_medicion(medicion)


@router.get("/sensores/{sensor_id}/mediciones", response_model=list[MedicionRespuesta])
def listar_mediciones(
    sensor_id: int = Path(gt=0),
    magnitud: str | None = Query(None, description="Nombre de la magnitud, ej: co2 o temperature"),
    desde: datetime | None = Query(None, description="Fecha inicial. Sin zona horaria = hora Colombia"),
    hasta: datetime | None = Query(None, description="Fecha final. Sin zona horaria = hora Colombia"),
    limit: int | None = Query(None, ge=1, le=1000, description="Ultimas N mediciones"),
    db: Session = Depends(get_db),
):
    """Historico de mediciones de un sensor. Los filtros se pueden combinar."""
    verificar_sensor(db, sensor_id)

    # Se pasan las fechas a UTC porque asi estan guardadas en la base
    desde_utc = a_utc(desde) if desde else None
    hasta_utc = a_utc(hasta) if hasta else None
    if desde_utc and hasta_utc and desde_utc > hasta_utc:
        raise HTTPException(
            status_code=400,
            detail="Rango de fechas invalido: 'desde' no puede ser mayor que 'hasta'",
        )

    sensor_magnitud_id = None
    if magnitud is not None:
        sensor_magnitud = crud_magnitud.obtener_magnitud_de_sensor(db, sensor_id, magnitud)
        if sensor_magnitud is None:
            raise HTTPException(
                status_code=400,
                detail=f"El sensor {sensor_id} no mide la magnitud '{magnitud}'",
            )
        sensor_magnitud_id = sensor_magnitud.id

    mediciones = crud_medicion.listar_mediciones(
        db, sensor_id, sensor_magnitud_id, desde_utc, hasta_utc, limit
    )
    return [convertir_medicion(m) for m in mediciones]


@router.get("/sensores/{sensor_id}/ultima-medicion", response_model=list[MedicionRespuesta])
def obtener_ultima_medicion(
    sensor_id: int = Path(gt=0),
    db: Session = Depends(get_db),
):
    """Ultimo mensaje guardado del sensor (una fila por cada magnitud)."""
    verificar_sensor(db, sensor_id)
    mediciones = crud_medicion.obtener_ultima_medicion(db, sensor_id)
    if not mediciones:
        raise HTTPException(
            status_code=404, detail=f"El sensor {sensor_id} todavia no tiene mediciones"
        )
    return [convertir_medicion(m) for m in mediciones]

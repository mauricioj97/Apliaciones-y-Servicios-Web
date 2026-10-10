"""Endpoints de consulta de magnitudes de los sensores."""

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.crud import sensor as crud_sensor
from app.crud import sensor_magnitud as crud_magnitud
from app.database.connection import get_db
from app.schemas.sensor_magnitud import SensorMagnitudRespuesta

router = APIRouter(tags=["Magnitudes"])


@router.get("/sensores/{sensor_id}/magnitudes", response_model=list[SensorMagnitudRespuesta])
def listar_magnitudes_de_sensor(
    sensor_id: int = Path(gt=0),
    db: Session = Depends(get_db),
):
    """Lista las magnitudes (con unidad y rango permitido) que mide un sensor."""
    if crud_sensor.obtener_sensor(db, sensor_id) is None:
        raise HTTPException(status_code=404, detail=f"No existe un sensor con id {sensor_id}")
    return crud_magnitud.listar_magnitudes_de_sensor(db, sensor_id)


@router.get("/sensor-magnitudes/{sensor_magnitud_id}", response_model=SensorMagnitudRespuesta)
def obtener_sensor_magnitud(
    sensor_magnitud_id: int = Path(gt=0),
    db: Session = Depends(get_db),
):
    """Consulta una magnitud por su id."""
    magnitud = crud_magnitud.obtener_sensor_magnitud(db, sensor_magnitud_id)
    if magnitud is None:
        raise HTTPException(
            status_code=404, detail=f"No existe una magnitud con id {sensor_magnitud_id}"
        )
    return magnitud

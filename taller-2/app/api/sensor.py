"""Endpoints de consulta de sensores."""

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.crud import sensor as crud_sensor
from app.database.connection import get_db
from app.schemas.sensor import SensorRespuesta

router = APIRouter(prefix="/sensores", tags=["Sensores"])


@router.get("", response_model=list[SensorRespuesta])
def listar_sensores(db: Session = Depends(get_db)):
    """Lista todos los sensores del catalogo."""
    return crud_sensor.listar_sensores(db)


@router.get("/por-codigo/{codigo}", response_model=SensorRespuesta)
def obtener_sensor_por_codigo(
    codigo: str = Path(min_length=1, max_length=20, description="Ej: GAS-006"),
    db: Session = Depends(get_db),
):
    """Busca un sensor por su codigo (el mismo sensor_id que llega por MQTT)."""
    sensor = crud_sensor.obtener_sensor_por_codigo(db, codigo)
    if sensor is None:
        raise HTTPException(status_code=404, detail=f"No existe un sensor con codigo '{codigo}'")
    return sensor


@router.get("/{sensor_id}", response_model=SensorRespuesta)
def obtener_sensor(
    sensor_id: int = Path(gt=0, description="Id numerico del sensor (llave primaria)"),
    db: Session = Depends(get_db),
):
    """Busca un sensor por su id numerico."""
    sensor = crud_sensor.obtener_sensor(db, sensor_id)
    if sensor is None:
        raise HTTPException(status_code=404, detail=f"No existe un sensor con id {sensor_id}")
    return sensor

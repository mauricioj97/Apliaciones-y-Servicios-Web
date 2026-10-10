"""Operaciones sobre la tabla sensor_magnitudes.

Solo lectura: las magnitudes tambien son parte del catalogo del docente.
"""

from sqlalchemy.orm import Session

from app.models.sensor_magnitud import SensorMagnitud


def listar_magnitudes_de_sensor(db: Session, sensor_id: int) -> list[SensorMagnitud]:
    return (
        db.query(SensorMagnitud)
        .filter(SensorMagnitud.sensor_id == sensor_id)
        .order_by(SensorMagnitud.id)
        .all()
    )


def obtener_sensor_magnitud(db: Session, sensor_magnitud_id: int) -> SensorMagnitud | None:
    return db.get(SensorMagnitud, sensor_magnitud_id)


def obtener_magnitud_de_sensor(db: Session, sensor_id: int, magnitud: str) -> SensorMagnitud | None:
    """Busca una magnitud por nombre (ej: "co2") dentro de un sensor."""
    return (
        db.query(SensorMagnitud)
        .filter(SensorMagnitud.sensor_id == sensor_id, SensorMagnitud.magnitud == magnitud)
        .first()
    )

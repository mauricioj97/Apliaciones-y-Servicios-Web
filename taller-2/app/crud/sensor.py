"""Operaciones sobre la tabla sensores.

Solo lectura: el catalogo de sensores lo administra el docente,
la aplicacion NO puede crear, modificar ni eliminar sensores.
"""

from sqlalchemy.orm import Session

from app.models.sensor import Sensor


def listar_sensores(db: Session) -> list[Sensor]:
    return db.query(Sensor).order_by(Sensor.id).all()


def obtener_sensor(db: Session, sensor_id: int) -> Sensor | None:
    return db.get(Sensor, sensor_id)


def obtener_sensor_por_codigo(db: Session, codigo: str) -> Sensor | None:
    return db.query(Sensor).filter(Sensor.codigo == codigo).first()

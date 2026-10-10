"""Operaciones sobre la tabla mediciones.

Operaciones permitidas:
- Create: guardar las mediciones que pasaron todas las validaciones.
- Read: consultar por id, historico con filtros y ultima medicion.
No se implementa Update ni Delete: un dato de un sensor no se debe cambiar.
"""

from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from app.models.medicion import Medicion
from app.models.sensor_magnitud import SensorMagnitud


def crear_mediciones(db: Session, mediciones: list[Medicion]) -> list[Medicion]:
    """Guarda todas las mediciones de un mismo mensaje en una sola transaccion.

    Si alguna falla, se hace rollback y no se guarda ninguna.
    """
    try:
        db.add_all(mediciones)
        db.commit()
    except Exception:
        db.rollback()
        raise
    for medicion in mediciones:
        db.refresh(medicion)
    return mediciones


def obtener_medicion(db: Session, medicion_id: int) -> Medicion | None:
    return (
        db.query(Medicion)
        .options(joinedload(Medicion.sensor_magnitud))
        .filter(Medicion.id == medicion_id)
        .first()
    )


def listar_mediciones(
    db: Session,
    sensor_id: int,
    sensor_magnitud_id: int | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    limit: int | None = None,
) -> list[Medicion]:
    """Historico de un sensor. Todos los filtros son opcionales y se pueden combinar.

    Se ordena de la mas reciente a la mas antigua, asi "limit" entrega las ultimas N.
    """
    consulta = (
        db.query(Medicion)
        .join(Medicion.sensor_magnitud)
        .options(joinedload(Medicion.sensor_magnitud))
        .filter(SensorMagnitud.sensor_id == sensor_id)
    )
    if sensor_magnitud_id is not None:
        consulta = consulta.filter(Medicion.sensor_magnitud_id == sensor_magnitud_id)
    if desde is not None:
        consulta = consulta.filter(Medicion.timestamp_utc >= desde)
    if hasta is not None:
        consulta = consulta.filter(Medicion.timestamp_utc <= hasta)

    consulta = consulta.order_by(Medicion.timestamp_utc.desc(), Medicion.id.desc())
    if limit is not None:
        consulta = consulta.limit(limit)
    return consulta.all()


def obtener_ultima_medicion(db: Session, sensor_id: int) -> list[Medicion]:
    """Devuelve las mediciones del mensaje mas reciente del sensor.

    Como un mensaje trae varias magnitudes (ej: co2 y temperature) y todas
    comparten el mismo timestamp, se devuelven todas las de ese timestamp.
    """
    ultima = listar_mediciones(db, sensor_id, limit=1)
    if not ultima:
        return []
    return listar_mediciones(
        db, sensor_id, desde=ultima[0].timestamp_utc, hasta=ultima[0].timestamp_utc
    )

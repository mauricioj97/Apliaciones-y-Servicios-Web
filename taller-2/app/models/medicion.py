"""Modelo ORM de la tabla mediciones."""

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Medicion(Base):
    __tablename__ = "mediciones"

    id = Column(BigInteger, primary_key=True)
    # Clave foranea: cada medicion pertenece a una magnitud de un sensor
    sensor_magnitud_id = Column(
        Integer,
        ForeignKey("sensor_magnitudes.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    valor = Column(Numeric(12, 4), nullable=False)
    # Se guarda siempre en UTC (TIMESTAMPTZ)
    timestamp_utc = Column(DateTime(timezone=True), nullable=False)
    fecha_recepcion = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    sensor_magnitud = relationship("SensorMagnitud", back_populates="mediciones")

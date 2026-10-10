"""Modelo ORM de la tabla sensor_magnitudes."""

from sqlalchemy import Column, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.database.connection import Base


class SensorMagnitud(Base):
    __tablename__ = "sensor_magnitudes"

    id = Column(Integer, primary_key=True)
    # Clave foranea: cada magnitud pertenece a un sensor
    sensor_id = Column(
        Integer,
        ForeignKey("sensores.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    magnitud = Column(String(50), nullable=False)
    unidad = Column(String(20), nullable=False)
    valor_minimo = Column(Numeric(12, 4), nullable=False)
    valor_maximo = Column(Numeric(12, 4), nullable=False)

    # Lado "muchos" de sensores 1:N sensor_magnitudes
    sensor = relationship("Sensor", back_populates="magnitudes")
    # Una magnitud tiene muchas mediciones (relacion 1:N)
    mediciones = relationship("Medicion", back_populates="sensor_magnitud")

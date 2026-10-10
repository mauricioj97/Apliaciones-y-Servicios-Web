"""Logica que decide si un mensaje MQTT se guarda o se rechaza.

Pasos (en orden):
1. Decodificar el JSON.
2. Validar estructura, tipos y timestamp con Pydantic (MensajeSensor).
3. Validar contra la base de datos con el ORM:
   - el sensor existe,
   - el sensor esta activo,
   - el sensor del mensaje es el mismo del topico suscrito,
   - cada magnitud pertenece al sensor,
   - la unidad coincide,
   - el valor esta dentro del rango permitido.
4. Si TODO esta bien, guardar una fila por magnitud con el mismo timestamp.
"""

import json
import logging
from decimal import Decimal

from pydantic import ValidationError

from app.crud import medicion as crud_medicion
from app.crud import sensor as crud_sensor
from app.crud import sensor_magnitud as crud_magnitud
from app.database.connection import SessionLocal
from app.models.medicion import Medicion
from app.schemas.medicion import MensajeSensor

log = logging.getLogger("mqtt")


def sensor_del_topico(topico: str) -> str | None:
    """De 'iot/sensors/GAS-006/data' saca 'GAS-006'."""
    partes = topico.split("/")
    if len(partes) == 4 and partes[0] == "iot" and partes[1] == "sensors" and partes[3] == "data":
        return partes[2]
    return None


def procesar_mensaje(texto: str, topico: str) -> tuple[bool, str]:
    """Procesa un mensaje. Devuelve (True, detalle) si se guardo o (False, motivo) si no."""

    # 1. JSON
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as error:
        return rechazar(f"El mensaje no es un JSON valido: {error}", texto)

    # 2. Pydantic: estructura, campos obligatorios, tipos y timestamp
    try:
        mensaje = MensajeSensor.model_validate(datos)
    except ValidationError as error:
        errores = "; ".join(
            f"{'.'.join(str(x) for x in e['loc'])}: {e['msg']}" for e in error.errors()
        )
        return rechazar(f"Error de estructura/tipo (Pydantic): {errores}", texto)

    # 3. Validaciones con la base de datos (ORM)
    db = SessionLocal()
    try:
        sensor = crud_sensor.obtener_sensor_por_codigo(db, mensaje.sensor_id)
        if sensor is None:
            return rechazar(
                f"Sensor inexistente: '{mensaje.sensor_id}' no esta en la tabla sensores", texto
            )

        if not sensor.activo:
            return rechazar(f"El sensor '{sensor.codigo}' esta inactivo", texto)

        esperado = sensor_del_topico(topico)
        if esperado is not None and esperado != sensor.codigo:
            return rechazar(
                f"El sensor_id '{sensor.codigo}' no corresponde al topico asignado ({esperado})",
                texto,
            )

        errores = []
        nuevas = []
        for nombre, medida in mensaje.measurements.items():
            config = crud_magnitud.obtener_magnitud_de_sensor(db, sensor.id, nombre)
            if config is None:
                errores.append(
                    f"Magnitud incorrecta: '{nombre}' no esta configurada para {sensor.codigo}"
                )
                continue
            if medida.unit != config.unidad:
                errores.append(
                    f"Unidad incorrecta en '{nombre}': llego '{medida.unit}' "
                    f"y se esperaba '{config.unidad}'"
                )
                continue
            valor = Decimal(str(medida.value))
            if valor < config.valor_minimo or valor > config.valor_maximo:
                errores.append(
                    f"Valor fuera de rango en '{nombre}': {valor} no esta entre "
                    f"{config.valor_minimo} y {config.valor_maximo}"
                )
                continue
            nuevas.append(
                Medicion(
                    sensor_magnitud_id=config.id,  # clave foranea a sensor_magnitudes
                    valor=valor,
                    timestamp_utc=mensaje.timestamp,  # mismo timestamp para todas
                )
            )

        # Regla del taller: si UNA magnitud falla, no se guarda NADA del mensaje
        if errores:
            return rechazar(" | ".join(errores), texto)

        # 4. Guardar
        guardadas = crud_medicion.crear_mediciones(db, nuevas)
        detalle = ", ".join(
            f"id={m.id} {m.sensor_magnitud.magnitud}={m.valor}" for m in guardadas
        )
        log.info(
            "[GUARDADO] %s | timestamp_utc=%s | %s",
            sensor.codigo,
            mensaje.timestamp.isoformat(),
            detalle,
        )
        return True, detalle
    except Exception as error:  # error de conexion u otro problema inesperado
        db.rollback()
        return rechazar(f"Error inesperado al guardar: {error}", texto)
    finally:
        db.close()


def rechazar(motivo: str, texto: str) -> tuple[bool, str]:
    """Escribe en el registro por que se rechazo el mensaje."""
    log.warning("[RECHAZADO] %s | payload=%s", motivo, texto)
    return False, motivo

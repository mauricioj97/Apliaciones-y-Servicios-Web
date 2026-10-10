"""Prueba las validaciones con mensajes invalidos hechos a mano.

Se llama directamente a la MISMA funcion que usa el cliente MQTT
(app/mqtt/procesador.py -> procesar_mensaje), asi no hay que publicar
nada en el broker y no se molesta a otros grupos.

Ejecutar desde la carpeta taller-2:
    python -m pruebas.probar_rechazos
"""

import json
import logging
import sys

from sqlalchemy import text

import app.models  # noqa: F401
from app.database.connection import SessionLocal
from app.mqtt.procesador import procesar_mensaje

TOPICO = "iot/sensors/GAS-006/data"
# Fecha "rara" para poder comprobar despues que nada se guardo con ella
TIMESTAMP_PRUEBA = "2000-01-01T00:00:00Z"


def mensaje(**cambios):
    """Arma un mensaje valido y le aplica los cambios de cada prueba."""
    base = {
        "sensor_id": "GAS-006",
        "timestamp": TIMESTAMP_PRUEBA,
        "measurements": {
            "co2": {"value": 800.5, "unit": "ppm"},
            "temperature": {"value": 24.6, "unit": "C"},
        },
    }
    base.update(cambios)
    return json.dumps(base)


PRUEBAS = [
    ("3. Sensor inexistente", mensaje(sensor_id="GAS-999")),
    ("4. Unidad incorrecta", mensaje(measurements={
        "co2": {"value": 800.5, "unit": "ppm"},
        "temperature": {"value": 24.6, "unit": "F"}})),
    ("5. Tipo de dato incorrecto (valor como texto)", mensaje(measurements={
        "co2": {"value": "800.5", "unit": "ppm"},
        "temperature": {"value": 24.6, "unit": "C"}})),
    ("6. Magnitud incorrecta", mensaje(measurements={
        "co2": {"value": 800.5, "unit": "ppm"},
        "humidity": {"value": 50, "unit": "%"}})),
    ("7a. Timestamp invalido (fecha imposible)", mensaje(timestamp="2026-13-45T25:61:00Z")),
    ("7b. Timestamp invalido (texto)", mensaje(timestamp="ayer en la tarde")),
    ("7c. Timestamp sin zona horaria UTC", mensaje(timestamp="2000-01-01T00:00:00")),
    ("Extra: valor fuera de rango", mensaje(measurements={
        "co2": {"value": 9000, "unit": "ppm"},
        "temperature": {"value": 24.6, "unit": "C"}})),
    ("Extra: falta un campo obligatorio", json.dumps({
        "sensor_id": "GAS-006", "timestamp": TIMESTAMP_PRUEBA})),
    ("Extra: sensor de otro grupo en nuestro topico", mensaje(sensor_id="GAS-001", measurements={
        "co": {"value": 10, "unit": "ppm"}})),
    ("Extra: JSON roto", '{"sensor_id": "GAS-006", "timestamp": '),
]


def contar_guardadas_con_timestamp_prueba() -> int:
    db = SessionLocal()
    try:
        return db.execute(
            text("SELECT COUNT(*) FROM mediciones WHERE timestamp_utc = :t"),
            {"t": TIMESTAMP_PRUEBA},
        ).scalar()
    finally:
        db.close()


def main():
    logging.basicConfig(level=logging.WARNING, format="    registro -> %(levelname)s %(message)s", stream=sys.stdout)
    antes = contar_guardadas_con_timestamp_prueba()
    print(f"Mediciones con timestamp {TIMESTAMP_PRUEBA} ANTES: {antes}\n")

    for nombre, payload in PRUEBAS:
        guardado, detalle = procesar_mensaje(payload, TOPICO)
        print("=" * 80)
        print(nombre)
        print(f"Entrada : {payload}")
        print(f"Guardado: {'SI' if guardado else 'NO (rechazado)'}")
        print(f"Motivo  : {detalle}")

    despues = contar_guardadas_con_timestamp_prueba()
    print("=" * 80)
    print(f"\nMediciones con timestamp {TIMESTAMP_PRUEBA} DESPUES: {despues}")
    print("OK: ningun mensaje invalido se guardo" if despues == antes else "ERROR: se guardo algo")


if __name__ == "__main__":
    main()

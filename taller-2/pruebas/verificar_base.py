"""Revisa directamente en PostgreSQL lo que guardo la aplicacion.

1. Cuantas mediciones hay del sensor GAS-006 y en que periodo.
2. Unas filas de ejemplo con el JOIN de las claves foraneas.
3. Que cada mensaje valido quedo con el MISMO timestamp para todas sus magnitudes.
4. Que los mensajes RECHAZADOS del registro (registros/mqtt.log) NO estan en la base.

Ejecutar desde la carpeta taller-2:
    python -m pruebas.verificar_base
"""

import json
from datetime import datetime

from sqlalchemy import text

from app.database.connection import SessionLocal
from app.utils.fechas import a_hora_colombia

CODIGO = "GAS-006"


def main():
    db = SessionLocal()
    try:
        print(f"=== 1. Resumen de mediciones guardadas para {CODIGO} ===")
        filas = db.execute(text("""
            SELECT sm.magnitud, sm.unidad, COUNT(*) AS cantidad,
                   MIN(m.timestamp_utc) AS primera, MAX(m.timestamp_utc) AS ultima,
                   MIN(m.valor) AS minimo, MAX(m.valor) AS maximo
            FROM mediciones m
            JOIN sensor_magnitudes sm ON sm.id = m.sensor_magnitud_id
            JOIN sensores s ON s.id = sm.sensor_id
            WHERE s.codigo = :codigo
            GROUP BY sm.magnitud, sm.unidad
            ORDER BY sm.magnitud
        """), {"codigo": CODIGO}).all()
        for f in filas:
            minutos = (f.ultima - f.primera).total_seconds() / 60
            print(f"- {f.magnitud} ({f.unidad}): {f.cantidad} registros | "
                  f"desde {a_hora_colombia(f.primera)} hasta {a_hora_colombia(f.ultima)} "
                  f"({minutos:.1f} minutos) | valores entre {f.minimo} y {f.maximo}")

        print("\n=== 2. Ultimas 6 filas con sus claves foraneas (JOIN) ===")
        filas = db.execute(text("""
            SELECT m.id, m.sensor_magnitud_id, sm.sensor_id, s.codigo, sm.magnitud,
                   m.valor, sm.unidad, m.timestamp_utc
            FROM mediciones m
            JOIN sensor_magnitudes sm ON sm.id = m.sensor_magnitud_id
            JOIN sensores s ON s.id = sm.sensor_id
            WHERE s.codigo = :codigo
            ORDER BY m.timestamp_utc DESC, m.id DESC
            LIMIT 6
        """), {"codigo": CODIGO}).all()
        print("id | sensor_magnitud_id (FK) | sensor_id (FK) | codigo | magnitud | valor | unidad | timestamp_utc")
        for f in filas:
            print(f"{f.id} | {f.sensor_magnitud_id} | {f.sensor_id} | {f.codigo} | {f.magnitud} | "
                  f"{f.valor} | {f.unidad} | {f.timestamp_utc.isoformat()}")

        print("\n=== 3. Mensajes guardados: cuantas magnitudes tiene cada timestamp ===")
        filas = db.execute(text("""
            SELECT cantidad, COUNT(*) AS mensajes FROM (
                SELECT m.timestamp_utc, COUNT(*) AS cantidad
                FROM mediciones m
                JOIN sensor_magnitudes sm ON sm.id = m.sensor_magnitud_id
                JOIN sensores s ON s.id = sm.sensor_id
                WHERE s.codigo = :codigo
                GROUP BY m.timestamp_utc
            ) t GROUP BY cantidad
        """), {"codigo": CODIGO}).all()
        for f in filas:
            print(f"- {f.mensajes} mensajes guardados con {f.cantidad} magnitudes cada uno")
        print("(Si todos tienen 2, ningun mensaje se guardo a medias)")

        print("\n=== 4. Mensajes RECHAZADOS en registros/mqtt.log que NO deben estar en la base ===")
        try:
            with open("registros/mqtt.log", encoding="utf-8") as archivo:
                lineas = [l for l in archivo if "[RECHAZADO]" in l]
        except FileNotFoundError:
            lineas = []
        revisados = 0
        for linea in lineas:
            motivo, _, payload = linea.partition("| payload=")
            motivo = motivo.split("[RECHAZADO]")[1].strip()
            try:
                timestamp = json.loads(payload)["timestamp"]
                fecha = datetime.fromisoformat(timestamp)
                assert fecha.tzinfo is not None
            except Exception:
                print(f"- (timestamp ilegible, imposible de guardar) motivo: {motivo}")
                continue
            cantidad = db.execute(text("""
                SELECT COUNT(*) FROM mediciones m
                JOIN sensor_magnitudes sm ON sm.id = m.sensor_magnitud_id
                JOIN sensores s ON s.id = sm.sensor_id
                WHERE s.codigo = :codigo AND m.timestamp_utc = :t
            """), {"codigo": CODIGO, "t": fecha}).scalar()
            revisados += 1
            estado = "NO esta en la base (correcto)" if cantidad == 0 else f"ERROR: hay {cantidad} filas"
            print(f"- {timestamp}: {estado} | motivo: {motivo}")
        print(f"Total de rechazados en el registro: {len(lineas)} (revisados por timestamp: {revisados})")
    finally:
        db.close()


if __name__ == "__main__":
    main()

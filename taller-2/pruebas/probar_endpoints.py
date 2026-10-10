"""Llama a todos los endpoints y guarda las respuestas como evidencia.

Primero hay que tener la API corriendo (uvicorn app.main:app).
Luego, desde la carpeta taller-2:
    python -m pruebas.probar_endpoints

Guarda cada respuesta en evidencias/http/ y un resumen en
evidencias/resultados_endpoints.md
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
SENSOR_ID = 33  # id de GAS-006 en la tabla sensores
CARPETA = os.path.join("evidencias", "http")


def llamar(ruta: str, parametros: dict | None = None):
    url = BASE + ruta
    if parametros:
        url += "?" + urllib.parse.urlencode(parametros)
    try:
        with urllib.request.urlopen(url) as respuesta:
            return url, respuesta.status, json.loads(respuesta.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return url, error.code, json.loads(error.read().decode("utf-8"))


def resumen(cuerpo) -> str:
    if isinstance(cuerpo, list):
        return f"lista con {len(cuerpo)} elementos"
    if isinstance(cuerpo, dict) and "detail" in cuerpo:
        detalle = cuerpo["detail"]
        if isinstance(detalle, list):
            detalle = "; ".join(f"{'.'.join(map(str, d['loc']))}: {d['msg']}" for d in detalle)
        return f"detail: {detalle}"
    return "objeto"


def main():
    os.makedirs(CARPETA, exist_ok=True)
    filas = []

    def prueba(numero, nombre, esperado, ruta, parametros=None):
        url, codigo, cuerpo = llamar(ruta, parametros)
        archivo = os.path.join(CARPETA, f"{numero}.json")
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(
                {"prueba": nombre, "url": url, "codigo_http": codigo, "respuesta": cuerpo},
                f, indent=2, ensure_ascii=False,
            )
        ok = "OK" if codigo == esperado else "FALLO"
        print(f"[{ok}] {codigo} {nombre} -> {resumen(cuerpo)}")
        filas.append((numero, nombre, url.replace(BASE, ""), esperado, codigo, ok, resumen(cuerpo)))
        return cuerpo

    # --- Catalogo ---
    prueba("01_sensores", "Listar sensores", 200, "/sensores")
    prueba("02_sensor_por_id", "Sensor por ID existente", 200, f"/sensores/{SENSOR_ID}")
    prueba("03_sensor_por_codigo", "Sensor por codigo", 200, "/sensores/por-codigo/GAS-006")
    prueba("04_sensor_id_inexistente", "Sensor por ID inexistente", 404, "/sensores/99999")
    prueba("05_sensor_codigo_inexistente", "Sensor por codigo inexistente", 404, "/sensores/por-codigo/NO-EXISTE")
    prueba("06_magnitudes_sensor", "Magnitudes del sensor (claves foraneas)", 200, f"/sensores/{SENSOR_ID}/magnitudes")
    prueba("07_sensor_magnitud", "Sensor-magnitud por ID", 200, "/sensor-magnitudes/88")
    prueba("08_sensor_magnitud_inexistente", "Sensor-magnitud inexistente", 404, "/sensor-magnitudes/99999")

    # --- Mediciones ---
    ultima = prueba("09_ultima_medicion", "Ultima medicion", 200, f"/sensores/{SENSOR_ID}/ultima-medicion")
    id_existente = ultima[0]["id"]
    prueba("10_medicion_por_id", "Medicion por ID existente", 200, f"/mediciones/{id_existente}")
    prueba("11_medicion_inexistente", "Medicion por ID inexistente", 404, "/mediciones/999999999")
    historico = prueba("12_historico", "Consulta historica completa", 200, f"/sensores/{SENSOR_ID}/mediciones")
    prueba("13_ultimas_10", "Ultimas N mediciones (limit=10)", 200, f"/sensores/{SENSOR_ID}/mediciones", {"limit": 10})
    prueba("14_filtro_magnitud", "Filtro por magnitud (co2)", 200, f"/sensores/{SENSOR_ID}/mediciones", {"magnitud": "co2", "limit": 20})

    # Rango de 5 minutos dentro de lo recolectado (en hora de Colombia)
    mas_antigua = historico[-1]["timestamp_colombia"][:19]
    inicio = datetime.strptime(mas_antigua, "%Y-%m-%d %H:%M:%S")
    desde = inicio.replace(second=0).isoformat()
    hasta = (inicio.replace(second=0) + timedelta(minutes=5)).isoformat()
    prueba("15_rango_fechas", "Rango de fechas (5 minutos)", 200, f"/sensores/{SENSOR_ID}/mediciones", {"desde": desde, "hasta": hasta})
    prueba("16_filtros_combinados", "Magnitud + rango + limit", 200, f"/sensores/{SENSOR_ID}/mediciones",
           {"magnitud": "temperature", "desde": desde, "hasta": hasta, "limit": 10})

    # --- Errores ---
    prueba("17_rango_invertido", "Rango desde > hasta", 400, f"/sensores/{SENSOR_ID}/mediciones", {"desde": hasta, "hasta": desde})
    prueba("18_magnitud_no_existe", "Magnitud que el sensor no mide", 400, f"/sensores/{SENSOR_ID}/mediciones", {"magnitud": "humidity"})
    prueba("19_id_texto", "ID no numerico", 422, "/sensores/abc")
    prueba("20_limit_cero", "limit=0 (fuera del minimo)", 422, f"/sensores/{SENSOR_ID}/mediciones", {"limit": 0})
    prueba("21_fecha_mal_escrita", "desde con formato invalido", 422, f"/sensores/{SENSOR_ID}/mediciones", {"desde": "ayer"})

    with open(os.path.join("evidencias", "resultados_endpoints.md"), "w", encoding="utf-8") as f:
        f.write("# Resultados de las pruebas HTTP\n\n")
        f.write(f"Generado automaticamente por `pruebas/probar_endpoints.py` el "
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (hora Colombia).\n\n")
        f.write("| Archivo | Prueba | Solicitud | Esperado | Obtenido | Estado | Resumen |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for numero, nombre, url, esperado, codigo, ok, res in filas:
            url = url.replace("|", "%7C")
            f.write(f"| [`{numero}.json`](http/{numero}.json) | {nombre} | `GET {url}` | {esperado} | {codigo} | {ok} | {res} |\n")
    print("\nResumen guardado en evidencias/resultados_endpoints.md")


if __name__ == "__main__":
    main()

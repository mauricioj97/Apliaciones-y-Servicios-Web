"""Clase 4 — Datos e interacción entre aplicaciones.

Flujo: estudiantes.csv → estructuras de Python → transformación → estudiantes_resumen.json
"""

import csv
import json
from pathlib import Path

# Paso 1 — Verificar Python
print("Hola, Aplicaciones y Servicios Web")

BASE_DIR = Path(__file__).resolve().parent
RUTA_CSV = BASE_DIR / "datos" / "estudiantes.csv"
RUTA_JSON = BASE_DIR / "salida" / "estudiantes_resumen.json"


# Paso 2 — Leer el CSV
def leer_estudiantes(ruta: Path) -> list[dict]:
    """Lee el CSV y devuelve cada fila como un diccionario Python."""
    with open(ruta, encoding="utf-8", newline="") as archivo:
        return list(csv.DictReader(archivo))


# Pasos 3 y 4 — Transformar un estudiante mediante una función
def transformar_estudiante(fila: dict) -> dict:
    """Convierte una fila del CSV al formato del panel académico.

    - codigo            → id
    - nombre + apellido → nombre_completo
    - semestre (texto)  → semestre (int)
    - promedio (texto)  → promedio (float)
    - activo true/false → estado Activo/Inactivo
    - correo            → se omite
    """
    return {
        "id": fila["codigo"],
        "nombre_completo": f"{fila['nombre'].strip()} {fila['apellido'].strip()}",
        "programa": fila["programa"],
        "semestre": int(fila["semestre"]),
        "promedio": float(fila["promedio"]),
        "estado": "Activo" if fila["activo"].strip().lower() == "true" else "Inactivo",
    }


# Paso 5 — Transformar todos los registros y guardarlos en una lista
def transformar_estudiantes(filas: list[dict]) -> list[dict]:
    """Aplica la transformación a todos los registros."""
    return [transformar_estudiante(fila) for fila in filas]


# Paso 6 — Serializar y guardar el JSON
def serializar_estudiantes(ruta: Path, estudiantes: list[dict]) -> None:
    """Serializa una lista de diccionarios Python a un archivo JSON UTF-8."""
    ruta.parent.mkdir(exist_ok=True)

    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(estudiantes, archivo, indent=2, ensure_ascii=False)


# Paso 7 — Deserializar el JSON generado
def deserializar_estudiantes(ruta: Path) -> list[dict]:
    """Deserializa un archivo JSON a una lista de diccionarios Python."""
    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)


# ---- Flujo principal ----
estudiantes = leer_estudiantes(RUTA_CSV)
print(f"\nRegistros leídos del CSV: {len(estudiantes)}")
print("Primer registro (CSV):", estudiantes[0])

estudiantes_transformados = transformar_estudiantes(estudiantes)
print("\nPrimer registro transformado:", estudiantes_transformados[0])
print(f"Total transformados: {len(estudiantes_transformados)}")

serializar_estudiantes(RUTA_JSON, estudiantes_transformados)
print(f"\nArchivo JSON generado: {RUTA_JSON}")

estudiantes_recuperados = deserializar_estudiantes(RUTA_JSON)

print("\nDatos recuperados desde el JSON:")
print(estudiantes_recuperados[0])
print(f"Total recuperado: {len(estudiantes_recuperados)}")

"""Punto de entrada de la API.

Ejecutar desde la carpeta taller-2:
    uvicorn app.main:app
Documentacion interactiva: http://127.0.0.1:8000/docs
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.models  # noqa: F401  (registra los modelos y sus relaciones)
from app.api import medicion, sensor, sensor_magnitud
from app.mqtt.client import iniciar_en_segundo_plano


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    """Al iniciar la API se arranca el consumidor MQTT y al apagarla se detiene."""
    cliente = None
    if os.getenv("MQTT_ENABLED", "true").lower() == "true":
        cliente = iniciar_en_segundo_plano()
    yield
    if cliente is not None:
        cliente.loop_stop()
        cliente.disconnect()


app = FastAPI(
    title="API IoT - Taller 2",
    description="Recibe datos del sensor GAS-006 por MQTT, los valida, "
    "los guarda en PostgreSQL y permite consultarlos.",
    version="1.0.0",
    lifespan=ciclo_de_vida,
)

app.include_router(sensor.router)
app.include_router(sensor_magnitud.router)
app.include_router(medicion.router)


@app.get("/", tags=["Inicio"])
def inicio():
    return {"mensaje": "API IoT Taller 2 funcionando. Ver /docs"}

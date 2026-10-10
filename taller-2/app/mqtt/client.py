"""Cliente MQTT: se conecta al broker, se suscribe al topico y procesa cada mensaje.

Se puede usar de dos formas:
- Automaticamente al iniciar la API (ver app/main.py, MQTT_ENABLED=true).
- Solo, sin la API:  python -m app.mqtt.client
"""

import logging
import os

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

from app.mqtt.procesador import procesar_mensaje

load_dotenv()

BROKER = os.getenv("MQTT_BROKER")
PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = os.getenv("MQTT_TOPIC")
USERNAME = os.getenv("MQTT_USERNAME")
PASSWORD = os.getenv("MQTT_PASSWORD")
KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", "60"))

log = logging.getLogger("mqtt")


def configurar_registros():
    """Muestra los registros en consola y tambien los guarda en registros/mqtt.log"""
    if log.handlers:
        return
    os.makedirs("registros", exist_ok=True)
    formato = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    consola = logging.StreamHandler()
    consola.setFormatter(formato)
    archivo = logging.FileHandler("registros/mqtt.log", encoding="utf-8")
    archivo.setFormatter(formato)
    log.addHandler(consola)
    log.addHandler(archivo)
    log.setLevel(logging.INFO)
    log.propagate = False


def on_connect(client, userdata, flags, reason_code, properties=None):
    """Se ejecuta cuando el cliente se conecta al broker."""
    if reason_code != 0:
        log.error("Error de conexion MQTT: %s", reason_code)
        return
    log.info("Conectado al broker %s:%s", BROKER, PORT)
    client.subscribe(TOPIC)
    log.info("Suscrito al topico: %s", TOPIC)


def on_message(client, userdata, message):
    """Se ejecuta cada vez que llega un mensaje al topico."""
    try:
        texto = message.payload.decode("utf-8")
    except UnicodeDecodeError:
        log.warning("[RECHAZADO] El mensaje no esta en UTF-8 | payload=%r", message.payload)
        return
    log.info("[RECIBIDO] %s | %s", message.topic, texto)
    procesar_mensaje(texto, message.topic)


def crear_cliente() -> mqtt.Client:
    if not BROKER or not TOPIC:
        raise RuntimeError("Faltan MQTT_BROKER o MQTT_TOPIC en el archivo .env")
    configurar_registros()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if USERNAME:
        client.username_pw_set(USERNAME, PASSWORD or "")
    client.on_connect = on_connect
    client.on_message = on_message
    return client


def iniciar_en_segundo_plano() -> mqtt.Client:
    """Arranca el cliente en un hilo aparte (lo usa la API al iniciar)."""
    client = crear_cliente()
    client.connect_async(BROKER, PORT, KEEPALIVE)
    client.loop_start()
    return client


if __name__ == "__main__":
    import app.models  # noqa: F401  (registra los modelos y sus relaciones)

    cliente = crear_cliente()
    log.info("Conectando a %s:%s ...", BROKER, PORT)
    cliente.connect(BROKER, PORT, KEEPALIVE)
    try:
        cliente.loop_forever()
    except KeyboardInterrupt:
        log.info("Consumidor detenido por el usuario")

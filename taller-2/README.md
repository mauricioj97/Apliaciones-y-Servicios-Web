# Taller 2 — API para adquisición y consulta de datos IoT

**FastAPI + MQTT + Pydantic + SQLAlchemy ORM + PostgreSQL**

---

## 1. Información general

| Campo | Valor |
|---|---|
| **Nombre del proyecto** | API IoT — Adquisición, validación y consulta de datos del sensor GAS-006 |
| **Integrantes** | Mauricio Jojoa (trabajo individual) |
| **Asignatura** | Aplicaciones y Servicios Web |
| **Programa** | Tecnología en Desarrollo de Software |
| **Docente** | Juan Carlos Morales Guerra |
| **Guía** | 002 — Taller 2 |
| **Fecha** | 10 de octubre de 2026 |
| **Sensor asignado** | `GAS-006` — Dióxido de carbono (id `33` en la tabla `sensores`) |
| **Tópico MQTT utilizado** | `iot/sensors/GAS-006/data` |
| **Broker** | `emqx.coriotlab.co:1883` |

---

## 2. Descripción del sistema

### 2.1 Problema resuelto

Un sensor IoT publica cada 5 segundos, por MQTT, mediciones de CO₂ y temperatura de un laboratorio de fermentación. Algunos mensajes llegan **mal formados a propósito** (unidad inválida, valor como texto, campos faltantes). Se necesitaba una aplicación que:

1. se conecte al broker y se suscriba al tópico del sensor;
2. revise cada mensaje (estructura, tipos, timestamp, sensor, magnitud, unidad y rango);
3. guarde **solo** los mensajes completamente válidos en PostgreSQL;
4. permita consultar sensores, magnitudes y mediciones por medio de una API REST, mostrando la hora en **hora de Colombia**.

### 2.2 Arquitectura implementada

```mermaid
flowchart LR
    S[Sensor GAS-006] -->|publica JSON| B[Broker MQTT<br/>emqx.coriotlab.co]
    B -->|iot/sensors/GAS-006/data| C[mqtt/client.py]
    C --> P[mqtt/procesador.py]
    P --> PY[Pydantic<br/>schemas/medicion.py]
    P --> CR[crud/]
    CR --> M[models/ ORM]
    M --> DB[(PostgreSQL appdb)]
    P -. inválido .-> L[registros/mqtt.log]
    U[Cliente HTTP] --> A[FastAPI api/]
    A --> CR
```

- El **cliente MQTT** corre en un hilo aparte que se inicia junto con la API (`lifespan` en `app/main.py`).
- **Pydantic** valida la forma del mensaje; el **ORM** valida contra el catálogo de la base.
- **FastAPI** solo expone operaciones de **consulta** (GET).

### 2.3 Magnitudes y unidades recibidas

| id `sensor_magnitudes` | Magnitud | Unidad | Tipo de dato | Rango permitido |
|---|---|---|---|---|
| 88 | `co2` | `ppm` (partes por millón) | número decimal | 300 – 5000 |
| 87 | `temperature` | `C` (grados Celsius) | número decimal | -10 – 60 |

### 2.4 Payload real del sensor

```json
{
  "sensor_id": "GAS-006",
  "timestamp": "2026-10-10T19:43:15Z",
  "measurements": {
    "co2": { "value": 424.05, "unit": "ppm" },
    "temperature": { "value": 22.52, "unit": "C" }
  }
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `sensor_id` | string | Código del sensor; corresponde a `sensores.codigo` (no al `id` numérico). |
| `timestamp` | string ISO 8601 en UTC (`Z`) | Momento de la medición. |
| `measurements` | objeto | Una clave por magnitud. |
| `measurements.<magnitud>.value` | número | Valor medido. |
| `measurements.<magnitud>.unit` | string | Unidad de la magnitud. |

**Estructura:** un mensaje trae **2 magnitudes** que comparten el timestamp. **Frecuencia:** ~1 mensaje cada 5 s.

**Mensajes inválidos observados en el broker** (ver [`evidencias/registro_mqtt.txt`](evidencias/registro_mqtt.txt)):

| Error | Ejemplo real | Veces |
|---|---|---|
| Unidad inválida | `"co2": {"value": 1269.37, "unit": "INVALID_UNIT"}` | 3 |
| Valor como texto | `"co2": {"value": "730.94", "unit": "ppm"}` | 3 |
| Falta `unit` | `"temperature": {"value": 20.75}` | 5 |
| Falta `value` | `"temperature": {"unit": "C"}` | 2 |
| Magnitud no configurada | `"humidity": {"value": 33.74, "unit": "%"}` | 1 |
| Timestamp inválido | `"timestamp": "not-a-timestamp"` | 2 |
| Valor fuera de rango | `"co2": {"value": 999999.0, "unit": "ppm"}` | 1 |

---

## 3. Configuración del entorno

Todos los comandos se ejecutan dentro de la carpeta `taller-2` (Windows / PowerShell).

```bash
# 1. Crear y activar el entorno virtual
python -m venv .venv
.venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Crear el archivo de variables y llenarlo con los datos del docente
copy .env.example .env

# 4. Ejecutar la API (también inicia el consumidor MQTT)
uvicorn app.main:app
# Documentación interactiva: http://127.0.0.1:8000/docs
```

### `requirements.txt`

| Librería | Uso |
|---|---|
| `fastapi` | Framework de la API |
| `uvicorn[standard]` | Servidor para ejecutar la API |
| `SQLAlchemy` | ORM |
| `psycopg2-binary` | Driver de PostgreSQL |
| `pydantic` | Validación de datos |
| `paho-mqtt` | Cliente MQTT |
| `python-dotenv` | Lectura del archivo `.env` |

### Variables de entorno requeridas (sin valores sensibles)

| Variable | Descripción |
|---|---|
| `DB_HOST` | IP o host de PostgreSQL |
| `DB_PORT` | Puerto de PostgreSQL |
| `DB_NAME` | Nombre de la base (`appdb`) |
| `DB_USER` | Usuario de la base |
| `DB_PASSWORD` | Contraseña de la base |
| `MQTT_BROKER` | Host del broker MQTT |
| `MQTT_PORT` | Puerto del broker (1883) |
| `MQTT_TOPIC` | Tópico asignado (`iot/sensors/GAS-006/data`) |
| `MQTT_USERNAME` / `MQTT_PASSWORD` | Credenciales del broker (vacías, no se requieren) |
| `MQTT_KEEPALIVE` | Segundos de keepalive (60) |
| `MQTT_ENABLED` | `true` para que la API inicie el consumidor MQTT |

El archivo `.env` está en el `.gitignore` y **no** se sube al repositorio; solo se sube `.env.example`.

---

## 4. Base de datos

### 4.1 Conexión

`app/database/connection.py` arma la URL `postgresql+psycopg2://usuario:clave@host:puerto/base` con las variables del `.env`, crea el `engine` (con `pool_pre_ping`), la fábrica de sesiones `SessionLocal`, la clase `Base` para los modelos y la dependencia `get_db()` que abre y cierra una sesión por cada petición HTTP.

La aplicación **no crea tablas** (no usa `create_all`): las tablas y el catálogo ya existen y pertenecen al docente.

### 4.2 Tablas utilizadas

| Tabla | Uso en la aplicación | Modelo ORM |
|---|---|---|
| `sensores` | Solo lectura (catálogo) | `app/models/sensor.py` → `Sensor` |
| `sensor_magnitudes` | Solo lectura (catálogo, unidades y rangos) | `app/models/sensor_magnitud.py` → `SensorMagnitud` |
| `mediciones` | Inserción de mediciones válidas y consultas | `app/models/medicion.py` → `Medicion` |

### 4.3 Relaciones implementadas

```mermaid
erDiagram
    SENSORES ||--o{ SENSOR_MAGNITUDES : "1:N (sensor_id)"
    SENSOR_MAGNITUDES ||--o{ MEDICIONES : "1:N (sensor_magnitud_id)"
```

| Relación | FK en el modelo | `relationship` |
|---|---|---|
| `sensores` 1:N `sensor_magnitudes` | `SensorMagnitud.sensor_id = ForeignKey("sensores.id", onupdate="CASCADE", ondelete="RESTRICT")` | `Sensor.magnitudes` ↔ `SensorMagnitud.sensor` |
| `sensor_magnitudes` 1:N `mediciones` | `Medicion.sensor_magnitud_id = ForeignKey("sensor_magnitudes.id", onupdate="CASCADE", ondelete="RESTRICT")` | `SensorMagnitud.mediciones` ↔ `Medicion.sensor_magnitud` |

### 4.4 Correspondencia con `data-model.md`

| `data-model.md` | Modelo ORM |
|---|---|
| `SERIAL` / `BIGSERIAL` PK | `Column(Integer / BigInteger, primary_key=True)` |
| `VARCHAR(n)` | `String(n)` |
| `codigo UNIQUE` | `String(20), unique=True` |
| `BOOLEAN DEFAULT TRUE` | `Boolean, default=True` |
| `TIMESTAMPTZ DEFAULT NOW()` | `DateTime(timezone=True), server_default=func.now()` |
| `NUMERIC(12,4)` | `Numeric(12, 4)` |
| FK `ON UPDATE CASCADE ON DELETE RESTRICT` | `ForeignKey(..., onupdate="CASCADE", ondelete="RESTRICT")` |
| `NOT NULL` | `nullable=False` |

Cada medición guarda `sensor_magnitud_id` con el `id` real obtenido del catálogo, y `timestamp_utc` en UTC; `fecha_recepcion` la llena PostgreSQL (`DEFAULT NOW()`).

---

## 5. Organización del código

```text
taller-2/
├── app/
│   ├── main.py              # Crea la app FastAPI, registra routers e inicia MQTT
│   ├── database/connection.py
│   ├── models/              # sensor.py, sensor_magnitud.py, medicion.py
│   ├── schemas/             # sensor.py, sensor_magnitud.py, medicion.py
│   ├── crud/                # sensor.py, sensor_magnitud.py, medicion.py
│   ├── api/                 # sensor.py, sensor_magnitud.py, medicion.py
│   ├── mqtt/                # client.py, procesador.py
│   └── utils/fechas.py      # Conversión UTC <-> hora Colombia
├── pruebas/                 # Scripts que generan las evidencias
├── evidencias/              # Resultados de las pruebas
├── data-model.md · mqtt_example.py · requirements.txt · .env.example · .gitignore
```

| Carpeta | Función |
|---|---|
| `schemas/` | Esquemas **Pydantic**. `medicion.py` contiene `MensajeSensor` y `Medida`, que validan el payload MQTT (estructura, campos obligatorios, tipos estrictos, sin campos extra, timestamp ISO 8601 en UTC), y `MedicionRespuesta` para las respuestas. `sensor.py` y `sensor_magnitud.py` definen las respuestas de catálogo. |
| `models/` | Modelos **SQLAlchemy ORM** que representan las tres tablas, con sus claves primarias, foráneas y relaciones. |
| `crud/` | Acceso a datos. `sensor.py` y `sensor_magnitud.py` **solo leen** (el catálogo no se modifica). `medicion.py` **crea** (en una sola transacción) y **lee** (por id, histórico con filtros, última). No hay Update/Delete. |
| `api/` | Routers de **FastAPI**: definen rutas, parámetros, validación de parámetros (422) y errores 400/404 con `HTTPException`. No contienen SQL. |
| `mqtt/` | `client.py`: conexión al broker, suscripción y recepción (`on_connect`, `on_message`), registros en `registros/mqtt.log`. `procesador.py`: `procesar_mensaje()` aplica todas las validaciones y decide guardar o rechazar. |
| `database/` | Conexión a PostgreSQL, sesiones y `get_db()`. |

---

## 6. Endpoints implementados

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/sensores` | Lista todos los sensores. |
| GET | `/sensores/{id}` | Consulta un sensor por id. `404` si no existe; `422` si el id no es un entero positivo. |
| GET | `/sensores/por-codigo/{codigo}` | Consulta un sensor por su código (ej. `GAS-006`). `404` si no existe. |
| GET | `/sensores/{id}/magnitudes` | Lista las magnitudes del sensor con unidad y rango. `404` si el sensor no existe. |
| GET | `/sensor-magnitudes/{id}` | Consulta una magnitud por id. `404` si no existe. |
| GET | `/mediciones/{id}` | Consulta una medición por id (incluye magnitud, unidad, hora UTC y hora Colombia). `404` si no existe. |
| GET | `/sensores/{id}/mediciones` | Histórico del sensor, de la más reciente a la más antigua. Filtros combinables: `magnitud`, `desde`, `hasta`, `limit` (1–1000). `400` si `desde > hasta` o si el sensor no mide esa magnitud; `422` si un parámetro tiene formato inválido. |
| GET | `/sensores/{id}/ultima-medicion` | Último mensaje almacenado del sensor (una fila por magnitud, mismo timestamp). `404` si no hay mediciones. |

**Fechas:** las mediciones se guardan en UTC y se responden con `timestamp_utc` y `timestamp_colombia` (`AAAA-MM-DD HH:MM:SS (UTC-05:00)`). Los filtros `desde`/`hasta` sin zona horaria se interpretan en hora de Colombia.

Ejemplos:

```text
GET /sensores/33/mediciones?desde=2026-10-10T14:50:00&hasta=2026-10-10T14:55:00
GET /sensores/33/mediciones?magnitud=co2
GET /sensores/33/mediciones?limit=10
GET /sensores/33/mediciones?magnitud=temperature&desde=2026-10-10T14:50:00&hasta=2026-10-10T14:55:00&limit=10
```

---

## 7. Evidencias de funcionamiento

Todas las evidencias están en la carpeta [`evidencias/`](evidencias/README.md), con el detalle de **datos de entrada, resultado, código HTTP, registro almacenado/rechazado, archivo y función** de cada prueba.

**Recolección:** 10/10/2026 de **14:48:55 a 15:13:26** (hora Colombia) = **24,5 minutos**. Se recibieron **295** mensajes: **278 guardados** (556 filas en `mediciones`) y **17 rechazados**, ninguno de los cuales quedó en la base.

| # | Prueba | Resultado | Evidencia | Archivo → función |
|---|---|---|---|---|
| 1 | Recepción MQTT | Mensajes recibidos del tópico `iot/sensors/GAS-006/data` | [`registro_mqtt.txt`](evidencias/registro_mqtt.txt) | `app/mqtt/client.py` → `on_connect`, `on_message` |
| 2 | Medición válida | Almacenada (2 filas por mensaje) | [`registro_mqtt.txt`](evidencias/registro_mqtt.txt), [`verificacion_base.txt`](evidencias/verificacion_base.txt) | `app/mqtt/procesador.py` → `procesar_mensaje`; `app/crud/medicion.py` → `crear_mediciones` |
| 3 | Sensor inexistente | Rechazado | [`pruebas_rechazo_mqtt.txt`](evidencias/pruebas_rechazo_mqtt.txt) | `procesador.py` → `procesar_mensaje`; `crud/sensor.py` → `obtener_sensor_por_codigo` |
| 4 | Unidad incorrecta | Rechazado (prueba + mensajes reales `INVALID_UNIT`) | [`pruebas_rechazo_mqtt.txt`](evidencias/pruebas_rechazo_mqtt.txt), [`registro_mqtt.txt`](evidencias/registro_mqtt.txt) | `procesador.py` → `procesar_mensaje` |
| 5 | Tipo de dato incorrecto | Rechazado (prueba + mensajes reales con valor como texto) | [`pruebas_rechazo_mqtt.txt`](evidencias/pruebas_rechazo_mqtt.txt) | `schemas/medicion.py` → `Medida` (`strict=True`) |
| 6 | Magnitud incorrecta | Rechazado | [`pruebas_rechazo_mqtt.txt`](evidencias/pruebas_rechazo_mqtt.txt) | `crud/sensor_magnitud.py` → `obtener_magnitud_de_sensor` |
| 7 | Timestamp inválido | Rechazado (fecha imposible, texto, sin UTC) | [`pruebas_rechazo_mqtt.txt`](evidencias/pruebas_rechazo_mqtt.txt) | `schemas/medicion.py` → `timestamp_debe_ser_texto_iso`, `timestamp_debe_estar_en_utc` |
| 8 | Consulta por ID existente | `200` | [`http/02`](evidencias/http/02_sensor_por_id.json), [`http/10`](evidencias/http/10_medicion_por_id.json) | `api/sensor.py` → `obtener_sensor`; `api/medicion.py` → `obtener_medicion` |
| 9 | Consulta por ID inexistente | `404` | [`http/04`](evidencias/http/04_sensor_id_inexistente.json), [`http/11`](evidencias/http/11_medicion_inexistente.json) | mismas funciones, `HTTPException(404)` |
| 10 | Consulta histórica | `200` | [`http/12`](evidencias/http/12_historico.json) | `api/medicion.py` → `listar_mediciones`; `crud/medicion.py` → `listar_mediciones` |
| 11 | Rango de fechas | `200`, datos filtrados | [`http/15`](evidencias/http/15_rango_fechas.json) | `api/medicion.py` → `listar_mediciones`; `utils/fechas.py` → `a_utc` |
| 12 | Rango `desde > hasta` | `400` | [`http/17`](evidencias/http/17_rango_invertido.json) | `api/medicion.py` → `listar_mediciones` |
| 13 | Validación HTTP incorrecta | `422` | [`http/19`](evidencias/http/19_id_texto.json), [`http/20`](evidencias/http/20_limit_cero.json), [`http/21`](evidencias/http/21_fecha_mal_escrita.json) | Validación automática de FastAPI (`Path(gt=0)`, `Query(ge=1, le=1000)`, `datetime`) |
| 14 | Última medición | `200`, registro más reciente | [`http/09`](evidencias/http/09_ultima_medicion.json) | `api/medicion.py` → `obtener_ultima_medicion` |
| 15 | Últimas N mediciones | `200`, 10 filas | [`http/13`](evidencias/http/13_ultimas_10.json) | `crud/medicion.py` → `listar_mediciones` (`limit`) |
| 16 | Filtro por magnitud | `200`, solo `co2` | [`http/14`](evidencias/http/14_filtro_magnitud.json), [`http/16`](evidencias/http/16_filtros_combinados.json) | `crud/sensor_magnitud.py` → `obtener_magnitud_de_sensor` |
| 17 | Claves foráneas | Relación sensores → sensor_magnitudes → mediciones | [`http/06`](evidencias/http/06_magnitudes_sensor.json), [`verificacion_base.txt`](evidencias/verificacion_base.txt) | `models/*.py` (`ForeignKey`, `relationship`) |
| 18 | Separación de responsabilidades | Estructura modular | Sección 5 de este informe | `app/` |

Resumen automático de las 21 solicitudes HTTP: [`evidencias/resultados_endpoints.md`](evidencias/resultados_endpoints.md).

---

## 8. Control de versiones

- **Repositorio:** https://github.com/mauricioj97/Apliaciones-y-Servicios-Web/tree/taller-2
- **Rama:** `taller-2`
- **Evidencia de commits:**

| Commit | Fecha | Autor | Mensaje |
|---|---|---|---|
| `8efd571` | 2026-10-10 14:49 | Mauricio Jojoa | Taller 2: configuracion inicial (requirements, .gitignore, .env.example y modelo de datos) |
| `bf2f787` | 2026-10-10 14:49 | Mauricio Jojoa | Taller 2: conexion a PostgreSQL y modelos ORM con claves foraneas |
| `c396432` | 2026-10-10 14:49 | Mauricio Jojoa | Taller 2: esquemas Pydantic para validar el payload MQTT y responder en hora de Colombia |
| `b7d50c0` | 2026-10-10 14:49 | Mauricio Jojoa | Taller 2: capa CRUD (solo lectura de catalogo, crear y consultar mediciones) |
| `6bfdf3d` | 2026-10-10 14:49 | Mauricio Jojoa | Taller 2: consumidor MQTT con validaciones de negocio y almacenamiento |
| `163f1e9` | 2026-10-10 14:49 | Mauricio Jojoa | Taller 2: endpoints FastAPI de sensores, magnitudes y mediciones |
| `d5ba834` | 2026-10-10 14:51 | Mauricio Jojoa | Taller 2: scripts de prueba para rechazos MQTT, endpoints y verificacion en la base |
| `015170d` | 2026-10-10 15:15 | Mauricio Jojoa | Taller 2: evidencias de recoleccion MQTT (24,5 min), rechazos, verificacion en base y pruebas HTTP |
| `f637f21` | 2026-10-10 15:15 | Mauricio Jojoa | Taller 2: informe README del taller e indice de ramas en la raiz |
| `153c4c1` | 2026-10-10 15:15 | Mauricio Jojoa | Taller 2: historial de commits en el informe y detalle de mensajes rechazados reales |
| `8bfeb6e` | 2026-10-10 15:24 | Mauricio Jojoa | Taller 2: se sube el registro MQTT como .txt (el .gitignore excluia los .log) |
| `ce95567` | 2026-10-10 15:35 | Mauricio Jojoa | Taller 2: ajuste del README |

Historial completo: https://github.com/mauricioj97/Apliaciones-y-Servicios-Web/commits/taller-2

### Aporte de cada integrante

| Integrante | Aporte |
|---|---|
| Mauricio Jojoa | Trabajo individual: configuración del entorno, modelos ORM, esquemas Pydantic, capa CRUD, endpoints FastAPI, cliente MQTT y validaciones, recolección de datos, pruebas, evidencias y documentación. |

---

## 9. Conclusiones

### Principales aprendizajes

- MQTT funciona con **publicar/suscribir**: la aplicación no pregunta por los datos, el broker se los entrega en cuanto el sensor publica. HTTP, en cambio, es **petición/respuesta**; en el taller se usaron los dos.
- Validar en **dos niveles** es necesario: Pydantic revisa la **forma** del mensaje sin tocar la base, y el ORM revisa que los datos **tengan sentido** según el catálogo (sensor, magnitud, unidad, rango).
- Con un ORM las tablas se manejan como clases de Python y las relaciones (claves foráneas) se recorren con atributos, por ejemplo `medicion.sensor_magnitud.magnitud`.
- Separar el código en `models`, `schemas`, `crud`, `api`, `mqtt` y `database` hace más fácil encontrar errores y cambiar una parte sin dañar las otras.
- Es importante guardar las fechas en **UTC** y convertirlas solo al mostrarlas (hora de Colombia = UTC − 5).
- Los códigos HTTP comunican qué pasó: **200** bien, **404** no existe, **400** petición ilógica, **422** formato inválido.

### Dificultades encontradas

- El comando `python -m venv` fallaba dentro de la carpeta sincronizada con OneDrive.
- Pydantic, por defecto, convertía el texto `"730.94"` en número, y el broker sí envía valores como texto a propósito.
- La base de datos es compartida y la tabla `mediciones` tiene muchos datos de otros grupos.
- Entender que el `sensor_id` del mensaje es el **código** y no el id numérico.

### Soluciones aplicadas

- Crear primero la carpeta `.venv` y luego el entorno con `--without-pip` + `ensurepip`.
- Activar el **modo estricto** de Pydantic (`strict=True`) y prohibir campos extra (`extra="forbid"`).
- Filtrar siempre por el sensor asignado haciendo `JOIN` con `sensor_magnitudes`.
- Buscar el sensor por `codigo` (`obtener_sensor_por_codigo`) y usar su `id` (33) para las relaciones.
- Hacer las pruebas de mensajes inválidos llamando directamente a `procesar_mensaje`, sin publicar en el broker, para no afectar a otros grupos.

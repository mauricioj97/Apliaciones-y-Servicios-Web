# 🧪 Evidencias de funcionamiento — Taller 2 (sensor GAS-006)

## Archivos de esta carpeta

| Archivo | Qué contiene | Cómo se generó |
|---|---|---|
| [`registro_mqtt.log`](registro_mqtt.log) | Registro completo de la recolección: cada mensaje `[RECIBIDO]`, `[GUARDADO]` o `[RECHAZADO]` con su motivo | La API corriendo (`uvicorn app.main:app`) del **10/10/2026 14:48:55 a 15:13:26** (hora Colombia) |
| [`verificacion_base.txt`](verificacion_base.txt) | Consultas directas a PostgreSQL: cantidades, JOIN de claves foráneas, regla "todo o nada" y comprobación de que los rechazados no están en la base | `python -m pruebas.verificar_base` |
| [`pruebas_rechazo_mqtt.txt`](pruebas_rechazo_mqtt.txt) | 11 mensajes inválidos de prueba procesados por la misma función del cliente MQTT | `python -m pruebas.probar_rechazos` |
| [`resultados_endpoints.md`](resultados_endpoints.md) | Tabla con las 21 solicitudes HTTP, código esperado y obtenido | `python -m pruebas.probar_endpoints` |
| [`http/`](http/) | Respuesta completa (URL, código HTTP y JSON) de cada solicitud | `python -m pruebas.probar_endpoints` |

## 📊 Resumen de la recolección

| Dato | Valor |
|---|---|
| Inicio | 2026-10-10 14:48:55 (hora Colombia) = 19:48:55 UTC |
| Fin | 2026-10-10 15:13:26 (hora Colombia) = 20:13:26 UTC |
| Duración | **24,5 minutos** (mínimo pedido: 20) |
| Mensajes recibidos | **295** |
| Mensajes guardados | **278** → **556** filas en `mediciones` (278 de `co2` + 278 de `temperature`) |
| Mensajes rechazados | **17** (ninguno quedó en la base) |
| Rango de valores guardados | co2: 352,55 – 1499,49 ppm · temperature: 18,03 – 31,99 °C |

### Mensajes inválidos reales enviados por el broker

| Tipo de error | Ejemplo real | Cantidad | Quién lo detectó |
|---|---|---|---|
| Unidad incorrecta | `"co2": {"value": 1269.37, "unit": "INVALID_UNIT"}` | 3 | ORM / lógica de negocio |
| Tipo de dato incorrecto | `"co2": {"value": "730.94", "unit": "ppm"}` | 3 | Pydantic (`strict=True`) |
| Falta la unidad | `"temperature": {"value": 20.75}` | 5 | Pydantic (campo obligatorio) |
| Falta el valor | `"temperature": {"unit": "C"}` | 2 | Pydantic (campo obligatorio) |
| Magnitud incorrecta | `"humidity": {"value": 33.74, "unit": "%"}` (junto a co2 y temperature válidos) | 1 | ORM / lógica de negocio |
| Timestamp inválido | `"timestamp": "not-a-timestamp"` | 2 | Pydantic (validador de timestamp) |
| Valor fuera de rango | `"co2": {"value": 999999, ...}` | 1 | ORM / lógica de negocio (rango) |

---

## ✅ Pruebas obligatorias (Actividad 6)

### 1. Recepción MQTT
- **Entrada:** suscripción al tópico `iot/sensors/GAS-006/data` en `emqx.coriotlab.co:1883`.
- **Resultado:** conexión exitosa y 295 mensajes recibidos (uno cada ~5 s).
  ```
  2026-10-10 14:48:55,558 INFO Conectado al broker emqx.coriotlab.co:1883
  2026-10-10 14:48:55,558 INFO Suscrito al topico: iot/sensors/GAS-006/data
  2026-10-10 14:48:56,009 INFO [RECIBIDO] iot/sensors/GAS-006/data | {"sensor_id": "GAS-006", "timestamp": "2026-10-10T19:48:55Z", "measurements": {"co2": {"value": 1168.91, "unit": "ppm"}, "temperature": {"value": 19.34, "unit": "C"}}}
  ```
- **Código HTTP:** no aplica (MQTT).
- **Archivo / función:** `app/mqtt/client.py` → `crear_cliente`, `on_connect`, `on_message`; arranque en `app/main.py` → `ciclo_de_vida`.
- **Explicación:** el cliente paho-mqtt se conecta al broker, se suscribe al tópico asignado y por cada mensaje ejecuta `on_message`.
- **Evidencia:** [`registro_mqtt.log`](registro_mqtt.log) (líneas `[RECIBIDO]`).

### 2. Medición válida
- **Entrada:** `{"sensor_id": "GAS-006", "timestamp": "2026-10-10T19:48:55Z", "measurements": {"co2": {"value": 1168.91, "unit": "ppm"}, "temperature": {"value": 19.34, "unit": "C"}}}`
- **Resultado:** **almacenado**: `[GUARDADO] GAS-006 | timestamp_utc=2026-10-10T19:48:55+00:00 | id=110745 co2=1168.9100, id=110746 temperature=19.3400`
- **Registro en PostgreSQL** (de `verificacion_base.txt`):
  ```
  id     | sensor_magnitud_id (FK) | sensor_id (FK) | codigo  | magnitud    | valor     | unidad | timestamp_utc
  112623 | 87                      | 33             | GAS-006 | temperature | 23.5500   | C      | 2026-10-10T20:13:26+00:00
  112622 | 88                      | 33             | GAS-006 | co2         | 1430.6800 | ppm    | 2026-10-10T20:13:26+00:00
  ```
  y `278 mensajes guardados con 2 magnitudes cada uno` (mismo `timestamp_utc` para ambas filas).
- **Archivo / función:** `app/mqtt/procesador.py` → `procesar_mensaje`; `app/crud/medicion.py` → `crear_mediciones`.
- **Explicación:** el mensaje pasó Pydantic y las validaciones de catálogo; se insertó una fila por magnitud en una sola transacción.

### 3. Sensor inexistente
- **Entrada:** `{"sensor_id": "GAS-999", "timestamp": "2000-01-01T00:00:00Z", "measurements": {"co2": {"value": 800.5, "unit": "ppm"}, "temperature": {"value": 24.6, "unit": "C"}}}`
- **Resultado:** **rechazado** — `Sensor inexistente: 'GAS-999' no esta en la tabla sensores`
- **Archivo / función:** `app/mqtt/procesador.py` → `procesar_mensaje`; `app/crud/sensor.py` → `obtener_sensor_por_codigo`.
- **Explicación:** se busca el `codigo` en la tabla `sensores` con el ORM; al no existir, no se guarda nada.
- **Evidencia:** [`pruebas_rechazo_mqtt.txt`](pruebas_rechazo_mqtt.txt) (prueba 3). Conteo de filas con ese timestamp: antes 0, después 0.

### 4. Unidad incorrecta
- **Entrada (prueba):** `"temperature": {"value": 24.6, "unit": "F"}` · **Entrada (real del broker):** `"co2": {"value": 1269.37, "unit": "INVALID_UNIT"}`
- **Resultado:** **rechazado** — `Unidad incorrecta en 'temperature': llego 'F' y se esperaba 'C'` / `Unidad incorrecta en 'co2': llego 'INVALID_UNIT' y se esperaba 'ppm'`
- **Archivo / función:** `app/mqtt/procesador.py` → `procesar_mensaje` (compara con `SensorMagnitud.unidad`).
- **Explicación:** la unidad recibida debe ser igual a la configurada en `sensor_magnitudes`. Aunque `co2` estuviera bien, el mensaje completo se descarta.
- **Evidencia:** [`pruebas_rechazo_mqtt.txt`](pruebas_rechazo_mqtt.txt) (prueba 4) y [`registro_mqtt.log`](registro_mqtt.log); `verificacion_base.txt` confirma que `2026-10-10T19:49:25Z` **no** está en la base.

### 5. Tipo de dato incorrecto
- **Entrada (prueba y real del broker):** `"co2": {"value": "730.94", "unit": "ppm"}` (número enviado como texto)
- **Resultado:** **rechazado** — `Error de estructura/tipo (Pydantic): measurements.co2.value: Input should be a valid number`
- **Archivo / función:** `app/schemas/medicion.py` → clase `Medida` (`strict=True`, `value: float`).
- **Explicación:** en modo estricto Pydantic no convierte texto a número, por eso detecta el tipo incorrecto.
- **Evidencia:** [`pruebas_rechazo_mqtt.txt`](pruebas_rechazo_mqtt.txt) (prueba 5) y [`registro_mqtt.log`](registro_mqtt.log) (19:53:11Z, 19:55:46Z, 20:01:16Z).

### 6. Magnitud incorrecta
- **Entrada (prueba):** `"co2": {...}, "humidity": {"value": 50, "unit": "%"}`
- **Entrada (real del broker, 19:58:16Z):** `{"co2": {"value": 926.24, "unit": "ppm"}, "temperature": {"value": 21.07, "unit": "C"}, "humidity": {"value": 33.74, "unit": "%"}}` → co2 y temperature eran válidos, pero por la regla "todo o nada" **no se guardó ninguna** de las tres.
- **Resultado:** **rechazado** — `Magnitud incorrecta: 'humidity' no esta configurada para GAS-006`
- **Archivo / función:** `app/crud/sensor_magnitud.py` → `obtener_magnitud_de_sensor`; `app/mqtt/procesador.py` → `procesar_mensaje`.
- **Explicación:** GAS-006 solo tiene `co2` y `temperature` en `sensor_magnitudes`; cualquier otra magnitud invalida el mensaje completo.
- **Evidencia:** [`pruebas_rechazo_mqtt.txt`](pruebas_rechazo_mqtt.txt) (prueba 6) y [`registro_mqtt.log`](registro_mqtt.log) (19:58:16Z).

### 7. Timestamp inválido
- **Entradas:** `"2026-13-45T25:61:00Z"` (fecha imposible), `"ayer en la tarde"` (texto), `"2000-01-01T00:00:00"` (sin UTC) y, real del broker, `"not-a-timestamp"`.
- **Resultado:** **rechazado** — `timestamp: Value error, '...' no es una fecha ISO 8601 valida` / `el timestamp debe estar en UTC (terminar en 'Z' o '+00:00')`
- **Archivo / función:** `app/schemas/medicion.py` → `MensajeSensor.timestamp_debe_ser_texto_iso` y `MensajeSensor.timestamp_debe_estar_en_utc`.
- **Explicación:** el timestamp debe ser texto ISO 8601 válido y estar en UTC.
- **Evidencia:** [`pruebas_rechazo_mqtt.txt`](pruebas_rechazo_mqtt.txt) (pruebas 7a, 7b, 7c) y [`registro_mqtt.log`](registro_mqtt.log).

### 8. Consulta por ID existente
- **Entrada:** `GET /sensores/33` y `GET /mediciones/112623`
- **Resultado:** `200`
  ```json
  {"id": 33, "codigo": "GAS-006", "nombre": "Dióxido de carbono", "categoria": "GAS", "ubicacion": "Laboratorio de fermentación", "activo": true, "fecha_registro": "2026-10-09 08:26:04 (UTC-05:00)"}
  ```
  ```json
  {"id": 112623, "sensor_magnitud_id": 87, "magnitud": "temperature", "unidad": "C", "valor": 23.55, "timestamp_utc": "2026-10-10T20:13:26Z", "timestamp_colombia": "2026-10-10 15:13:26 (UTC-05:00)", "fecha_recepcion_colombia": "2026-10-10 15:13:26 (UTC-05:00)"}
  ```
- **Archivo / función:** `app/api/sensor.py` → `obtener_sensor`; `app/api/medicion.py` → `obtener_medicion`; `app/crud/medicion.py` → `obtener_medicion`.
- **Evidencia:** [`http/02_sensor_por_id.json`](http/02_sensor_por_id.json), [`http/03_sensor_por_codigo.json`](http/03_sensor_por_codigo.json), [`http/07_sensor_magnitud.json`](http/07_sensor_magnitud.json), [`http/10_medicion_por_id.json`](http/10_medicion_por_id.json).

### 9. Consulta por ID inexistente
- **Entrada:** `GET /sensores/99999`, `GET /sensores/por-codigo/NO-EXISTE`, `GET /sensor-magnitudes/99999`, `GET /mediciones/999999999`
- **Resultado:** `404` — `{"detail": "No existe un sensor con id 99999"}`
- **Archivo / función:** mismas funciones de `app/api/` con `raise HTTPException(status_code=404, ...)`.
- **Evidencia:** [`http/04_sensor_id_inexistente.json`](http/04_sensor_id_inexistente.json), [`http/05_sensor_codigo_inexistente.json`](http/05_sensor_codigo_inexistente.json), [`http/08_sensor_magnitud_inexistente.json`](http/08_sensor_magnitud_inexistente.json), [`http/11_medicion_inexistente.json`](http/11_medicion_inexistente.json).

### 10. Consulta histórica
- **Entrada:** `GET /sensores/33/mediciones`
- **Resultado:** `200` — **556** mediciones, de la más reciente (15:13:26) a la más antigua (14:48:55).
- **Archivo / función:** `app/api/medicion.py` → `listar_mediciones`; `app/crud/medicion.py` → `listar_mediciones`.
- **Evidencia:** [`http/12_historico.json`](http/12_historico.json).

### 11. Consulta por rango de fechas
- **Entrada:** `GET /sensores/33/mediciones?desde=2026-10-10T14:48:00&hasta=2026-10-10T14:53:00` (hora Colombia)
- **Resultado:** `200` — **94** mediciones (47 mensajes), todas entre 14:48:55 y 14:52:56.
- **Archivo / función:** `app/api/medicion.py` → `listar_mediciones`; `app/utils/fechas.py` → `a_utc`; `app/crud/medicion.py` → `listar_mediciones`.
- **Explicación:** las fechas sin zona se toman como hora Colombia y se pasan a UTC (19:48–19:53 UTC) antes de filtrar.
- **Evidencia:** [`http/15_rango_fechas.json`](http/15_rango_fechas.json).

### 12. Rango `desde > hasta`
- **Entrada:** `GET /sensores/33/mediciones?desde=2026-10-10T14:53:00&hasta=2026-10-10T14:48:00`
- **Resultado:** `400` — `{"detail": "Rango de fechas invalido: 'desde' no puede ser mayor que 'hasta'"}`
- **Archivo / función:** `app/api/medicion.py` → `listar_mediciones`.
- **Evidencia:** [`http/17_rango_invertido.json`](http/17_rango_invertido.json). (Otro 400: magnitud que el sensor no mide → [`http/18_magnitud_no_existe.json`](http/18_magnitud_no_existe.json)).

### 13. Validación HTTP incorrecta
- **Entrada:** `GET /sensores/abc`, `GET /sensores/33/mediciones?limit=0`, `GET /sensores/33/mediciones?desde=ayer`
- **Resultado:** `422` — `path.sensor_id: Input should be a valid integer` / `query.limit: Input should be greater than or equal to 1` / `query.desde: Input should be a valid datetime`
- **Archivo / función:** validación automática de FastAPI por los tipos y restricciones de `app/api/*.py` (`int`, `Path(gt=0)`, `Query(ge=1, le=1000)`, `datetime`).
- **Evidencia:** [`http/19_id_texto.json`](http/19_id_texto.json), [`http/20_limit_cero.json`](http/20_limit_cero.json), [`http/21_fecha_mal_escrita.json`](http/21_fecha_mal_escrita.json).

### 14. Última medición
- **Entrada:** `GET /sensores/33/ultima-medicion`
- **Resultado:** `200` — las 2 filas del último mensaje (`id` 112623 temperature = 23,55 °C y 112622 co2 = 1430,68 ppm, ambas `2026-10-10 15:13:26` hora Colombia), que coincide con la última línea `[GUARDADO]` del registro.
- **Archivo / función:** `app/api/medicion.py` → `obtener_ultima_medicion`; `app/crud/medicion.py` → `obtener_ultima_medicion`.
- **Evidencia:** [`http/09_ultima_medicion.json`](http/09_ultima_medicion.json).

### 15. Últimas N mediciones
- **Entrada:** `GET /sensores/33/mediciones?limit=10`
- **Resultado:** `200` — exactamente **10** filas, de 15:13:26 a 15:13:06 (los 5 últimos mensajes).
- **Archivo / función:** `app/crud/medicion.py` → `listar_mediciones` (`ORDER BY timestamp_utc DESC` + `LIMIT`).
- **Evidencia:** [`http/13_ultimas_10.json`](http/13_ultimas_10.json).

### 16. Filtro por magnitud
- **Entrada:** `GET /sensores/33/mediciones?magnitud=co2&limit=20` y `GET /sensores/33/mediciones?magnitud=temperature&desde=2026-10-10T14:48:00&hasta=2026-10-10T14:53:00&limit=10`
- **Resultado:** `200` — 20 filas **solo de co2**; 10 filas **solo de temperature** dentro del rango (filtros combinados).
- **Archivo / función:** `app/api/medicion.py` → `listar_mediciones`; `app/crud/sensor_magnitud.py` → `obtener_magnitud_de_sensor`.
- **Evidencia:** [`http/14_filtro_magnitud.json`](http/14_filtro_magnitud.json), [`http/16_filtros_combinados.json`](http/16_filtros_combinados.json).

### 17. Claves foráneas
- **Entrada:** `GET /sensores/33/magnitudes` y consulta con JOIN en `verificacion_base.txt`.
- **Resultado:** `sensores.id = 33` → `sensor_magnitudes` 87 (temperature) y 88 (co2) con `sensor_id = 33` → cada medición guarda `sensor_magnitud_id` = 87 u 88.
- **Archivo / función:** `app/models/sensor_magnitud.py` (`ForeignKey("sensores.id")`), `app/models/medicion.py` (`ForeignKey("sensor_magnitudes.id")`), `relationship` en los tres modelos; `app/schemas/medicion.py` → `convertir_medicion` (usa `medicion.sensor_magnitud.magnitud`).
- **Evidencia:** [`http/06_magnitudes_sensor.json`](http/06_magnitudes_sensor.json), [`verificacion_base.txt`](verificacion_base.txt) (punto 2).

### 18. Separación de responsabilidades
- **Resultado:** cada tabla tiene su archivo en `schemas/`, `models/`, `crud/` y `api/`; MQTT en `mqtt/` y la conexión en `database/`.
- **Archivo / función:** carpeta `app/` (ver sección 5 del [README](../README.md)).
- **Explicación:** los endpoints no contienen SQL (llaman a `crud/`), `crud/` no sabe de HTTP, y la validación del payload está en `schemas/`.

---

## Comprobación de que los datos inválidos NO se almacenaron

1. **Pruebas controladas:** `pruebas_rechazo_mqtt.txt` cuenta las filas con el timestamp de prueba `2000-01-01T00:00:00Z` antes (0) y después (0) de procesar los 11 mensajes inválidos → `OK: ningun mensaje invalido se guardo`.
2. **Mensajes reales del broker:** `verificacion_base.txt` (punto 4) toma cada uno de los 17 `[RECHAZADO]` del registro y busca su timestamp en la base: los 15 con fecha legible dicen `NO esta en la base (correcto)`; los 2 con `"not-a-timestamp"` no se pueden guardar porque ni siquiera tienen fecha.
3. **Regla "todo o nada":** `verificacion_base.txt` (punto 3) muestra `278 mensajes guardados con 2 magnitudes cada uno` → ningún mensaje quedó guardado a medias.

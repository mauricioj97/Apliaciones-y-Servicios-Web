# Resultados de las pruebas HTTP

Generado automaticamente por `pruebas/probar_endpoints.py` el 2026-10-10 15:13:51 (hora Colombia).

| Archivo | Prueba | Solicitud | Esperado | Obtenido | Estado | Resumen |
|---|---|---|---|---|---|---|
| [`01_sensores.json`](http/01_sensores.json) | Listar sensores | `GET /sensores` | 200 | 200 | OK | lista con 25 elementos |
| [`02_sensor_por_id.json`](http/02_sensor_por_id.json) | Sensor por ID existente | `GET /sensores/33` | 200 | 200 | OK | objeto |
| [`03_sensor_por_codigo.json`](http/03_sensor_por_codigo.json) | Sensor por codigo | `GET /sensores/por-codigo/GAS-006` | 200 | 200 | OK | objeto |
| [`04_sensor_id_inexistente.json`](http/04_sensor_id_inexistente.json) | Sensor por ID inexistente | `GET /sensores/99999` | 404 | 404 | OK | detail: No existe un sensor con id 99999 |
| [`05_sensor_codigo_inexistente.json`](http/05_sensor_codigo_inexistente.json) | Sensor por codigo inexistente | `GET /sensores/por-codigo/NO-EXISTE` | 404 | 404 | OK | detail: No existe un sensor con codigo 'NO-EXISTE' |
| [`06_magnitudes_sensor.json`](http/06_magnitudes_sensor.json) | Magnitudes del sensor (claves foraneas) | `GET /sensores/33/magnitudes` | 200 | 200 | OK | lista con 2 elementos |
| [`07_sensor_magnitud.json`](http/07_sensor_magnitud.json) | Sensor-magnitud por ID | `GET /sensor-magnitudes/88` | 200 | 200 | OK | objeto |
| [`08_sensor_magnitud_inexistente.json`](http/08_sensor_magnitud_inexistente.json) | Sensor-magnitud inexistente | `GET /sensor-magnitudes/99999` | 404 | 404 | OK | detail: No existe una magnitud con id 99999 |
| [`09_ultima_medicion.json`](http/09_ultima_medicion.json) | Ultima medicion | `GET /sensores/33/ultima-medicion` | 200 | 200 | OK | lista con 2 elementos |
| [`10_medicion_por_id.json`](http/10_medicion_por_id.json) | Medicion por ID existente | `GET /mediciones/112623` | 200 | 200 | OK | objeto |
| [`11_medicion_inexistente.json`](http/11_medicion_inexistente.json) | Medicion por ID inexistente | `GET /mediciones/999999999` | 404 | 404 | OK | detail: No existe una medicion con id 999999999 |
| [`12_historico.json`](http/12_historico.json) | Consulta historica completa | `GET /sensores/33/mediciones` | 200 | 200 | OK | lista con 556 elementos |
| [`13_ultimas_10.json`](http/13_ultimas_10.json) | Ultimas N mediciones (limit=10) | `GET /sensores/33/mediciones?limit=10` | 200 | 200 | OK | lista con 10 elementos |
| [`14_filtro_magnitud.json`](http/14_filtro_magnitud.json) | Filtro por magnitud (co2) | `GET /sensores/33/mediciones?magnitud=co2&limit=20` | 200 | 200 | OK | lista con 20 elementos |
| [`15_rango_fechas.json`](http/15_rango_fechas.json) | Rango de fechas (5 minutos) | `GET /sensores/33/mediciones?desde=2026-10-10T14%3A48%3A00&hasta=2026-10-10T14%3A53%3A00` | 200 | 200 | OK | lista con 94 elementos |
| [`16_filtros_combinados.json`](http/16_filtros_combinados.json) | Magnitud + rango + limit | `GET /sensores/33/mediciones?magnitud=temperature&desde=2026-10-10T14%3A48%3A00&hasta=2026-10-10T14%3A53%3A00&limit=10` | 200 | 200 | OK | lista con 10 elementos |
| [`17_rango_invertido.json`](http/17_rango_invertido.json) | Rango desde > hasta | `GET /sensores/33/mediciones?desde=2026-10-10T14%3A53%3A00&hasta=2026-10-10T14%3A48%3A00` | 400 | 400 | OK | detail: Rango de fechas invalido: 'desde' no puede ser mayor que 'hasta' |
| [`18_magnitud_no_existe.json`](http/18_magnitud_no_existe.json) | Magnitud que el sensor no mide | `GET /sensores/33/mediciones?magnitud=humidity` | 400 | 400 | OK | detail: El sensor 33 no mide la magnitud 'humidity' |
| [`19_id_texto.json`](http/19_id_texto.json) | ID no numerico | `GET /sensores/abc` | 422 | 422 | OK | detail: path.sensor_id: Input should be a valid integer, unable to parse string as an integer |
| [`20_limit_cero.json`](http/20_limit_cero.json) | limit=0 (fuera del minimo) | `GET /sensores/33/mediciones?limit=0` | 422 | 422 | OK | detail: query.limit: Input should be greater than or equal to 1 |
| [`21_fecha_mal_escrita.json`](http/21_fecha_mal_escrita.json) | desde con formato invalido | `GET /sensores/33/mediciones?desde=ayer` | 422 | 422 | OK | detail: query.desde: Input should be a valid datetime or date, input is too short |

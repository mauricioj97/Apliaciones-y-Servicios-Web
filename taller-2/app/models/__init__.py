# Se importan los tres modelos aqui para que SQLAlchemy conozca
# todas las relaciones antes de hacer cualquier consulta.
from app.models.sensor import Sensor
from app.models.sensor_magnitud import SensorMagnitud
from app.models.medicion import Medicion

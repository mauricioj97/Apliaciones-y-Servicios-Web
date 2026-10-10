"""Conexion a la base de datos PostgreSQL usando SQLAlchemy.

Los datos de conexion se leen del archivo .env (nunca se escriben aqui).
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

if not DB_HOST or not DB_NAME or not DB_USER:
    raise RuntimeError("Faltan variables de la base de datos. Revisa el archivo .env")

# Formato: postgresql+psycopg2://usuario:clave@host:puerto/base
DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# pool_pre_ping revisa que la conexion siga viva antes de usarla
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Cada SessionLocal() es una "conversacion" con la base de datos
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Clase base de la que heredan todos los modelos ORM
Base = declarative_base()


def get_db():
    """Entrega una sesion a cada endpoint y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# app/database.py

import sqlite3
from pathlib import Path

from flask import current_app, g


def get_db():
    """Obtiene una conexión a la base de datos para la petición actual."""
    if "db" not in g:
        connection = sqlite3.connect(
            current_app.config["DATABASE"],
            timeout=10,
        )

        # Permite acceder a las columnas por su nombre.
        connection.row_factory = sqlite3.Row

        # Activa las relaciones entre tablas.
        connection.execute("PRAGMA foreign_keys = ON")

        g.db = connection

    return g.db


def close_db(exception=None):
    """Cierra la conexión si fue abierta durante la petición."""
    connection = g.pop("db", None)

    if connection is not None:
        connection.close()


def init_app(app):
    """Configura el almacenamiento y registra el cierre de conexiones."""
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    app.config.setdefault(
        "DATABASE",
        str(Path(app.instance_path) / "forratech.sqlite3"),
    )

    app.teardown_appcontext(close_db)

    # Comprueba la conexión y crea el archivo si todavía no existe.
    with app.app_context():
        get_db().execute("SELECT 1")
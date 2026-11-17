import mysql.connector
from mysql.connector import Error
from flask import current_app


def get_connection():
    """Abre uma conexão com o MySQL. Retorna None se der erro."""
    try:
        return mysql.connector.connect(
            host=current_app.config["DB_HOST"],
            port=current_app.config["DB_PORT"],
            user=current_app.config["DB_USER"],
            password=current_app.config["DB_PASSWORD"],
            database=current_app.config["DB_NAME"],
            charset="utf8mb4",
        )
    except Error as erro:
        current_app.logger.error("Erro ao conectar ao MySQL: %s", erro)
        return None

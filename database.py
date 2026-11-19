from contextlib import contextmanager

import mysql.connector
from mysql.connector import Error
from flask import current_app


class SemConexao(Exception):
    """Levantada quando não dá para abrir conexão com o MySQL (tratada em app.py)."""


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


@contextmanager
def sessao(dictionary=True):
    """
    Entrega (conexao, cursor) e fecha os dois sozinho ao sair do bloco `with`.
    Se o banco estiver fora do ar, levanta SemConexao (o app mostra uma tela de erro amigável).

        with sessao() as (con, cur):
            cur.execute("SELECT ...", (valor,))
            linhas = cur.fetchall()
    """
    conexao = get_connection()
    if conexao is None:
        raise SemConexao()
    cursor = conexao.cursor(dictionary=dictionary)
    try:
        yield conexao, cursor
    finally:
        cursor.close()
        conexao.close()

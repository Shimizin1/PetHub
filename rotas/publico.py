from flask import Blueprint, render_template

from database import sessao, SemConexao

bp = Blueprint("publico", __name__)


def _servicos():
    try:
        with sessao() as (_, cur):
            cur.execute("SELECT id, nome, preco, duracao_min FROM servicos ORDER BY nome")
            return cur.fetchall()
    except SemConexao:
        return []        # a vitrine continua abrindo mesmo sem banco


@bp.route("/")
def home():
    return render_template("publico/home.html", servicos=_servicos()[:6])


@bp.route("/servicos")
def servicos():
    return render_template("publico/servicos.html", servicos=_servicos())

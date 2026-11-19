from flask_login import UserMixin

from database import sessao


class Usuario(UserMixin):
    """Usuário logado. `cliente_id` só existe para o perfil 'cliente' (liga o login ao cadastro do dono)."""

    def __init__(self, id, nome, perfil, cliente_id=None):
        self.id = str(id)
        self.nome = nome
        self.perfil = perfil
        self.cliente_id = cliente_id


def carregar_por_id(user_id):
    try:
        with sessao() as (_, cur):
            cur.execute("SELECT id, nome, perfil, cliente_id FROM usuarios WHERE id = %s", (user_id,))
            linha = cur.fetchone()
    except Exception:
        return None
    return Usuario(linha["id"], linha["nome"], linha["perfil"], linha["cliente_id"]) if linha else None

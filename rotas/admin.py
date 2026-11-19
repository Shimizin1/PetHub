"""Painel da EQUIPE (/admin). Os CRUDs de /admin/clientes, /admin/pets... vêm de modulos.py + crud.py."""
from flask import Blueprint, render_template
from flask_login import current_user

from database import sessao, SemConexao
from permissoes import pode
from utilidades import saudacao_e_data

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
def dashboard():
    saudacao, hoje = saudacao_e_data()
    vazio = dict(total_clientes=0, total_pets=0, total_pendentes=0,
                 faturamento=None, proximos=[], hoje=hoje, saudacao=saudacao)
    try:
        with sessao() as (_, cur):
            cur.execute("SELECT COUNT(*) AS total FROM clientes")
            total_clientes = cur.fetchone()["total"]
            cur.execute("SELECT COUNT(*) AS total FROM pets")
            total_pets = cur.fetchone()["total"]
            cur.execute("SELECT COUNT(*) AS total FROM agendamentos WHERE status = 'Agendado'")
            total_pendentes = cur.fetchone()["total"]
            faturamento = None            # só o administrador enxerga o financeiro
            if pode(current_user.perfil, "financeiro", "listar"):
                cur.execute("""
                    SELECT COALESCE(SUM(s.preco), 0) AS total
                    FROM agendamentos a INNER JOIN servicos s ON s.id = a.servico_id
                    WHERE a.status = 'Concluído'
                """)
                faturamento = cur.fetchone()["total"]
            cur.execute("""
                SELECT a.id, a.data_hora, p.nome AS pet, c.nome AS dono, s.nome AS servico
                FROM agendamentos a
                INNER JOIN pets p ON p.id = a.pet_id
                INNER JOIN clientes c ON c.id = p.cliente_id
                INNER JOIN servicos s ON s.id = a.servico_id
                WHERE a.status = 'Agendado'
                ORDER BY a.data_hora LIMIT 5
            """)
            proximos = cur.fetchall()
        return render_template("admin/dashboard.html", erro=None, total_clientes=total_clientes,
                               total_pets=total_pets, total_pendentes=total_pendentes,
                               faturamento=faturamento, proximos=proximos,
                               hoje=hoje, saudacao=saudacao)
    except SemConexao:
        return render_template("admin/dashboard.html",
                               erro="Não foi possível conectar ao banco de dados.", **vazio)

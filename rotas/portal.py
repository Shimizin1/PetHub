"""
Área do CLIENTE (/cliente): painel, meus pets, meus agendamentos e meu perfil.

Regra de ouro: TODA consulta aqui filtra pelo cliente_id do usuário logado
(current_user.cliente_id). Mesmo que alguém troque o id na URL, só alcança o que é seu.
"""
from datetime import date, datetime, timedelta

import mysql.connector
from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, abort, current_app)
from flask_login import current_user
from werkzeug.security import check_password_hash, generate_password_hash

from database import sessao
from modulos import ESPECIES
from utilidades import saudacao_e_data

bp = Blueprint("portal", __name__, url_prefix="/cliente")

ANTECEDENCIA_MAX_DIAS = 90


# ---------------------------------------------------------------- painel
@bp.route("/")
def painel():
    saudacao, hoje = saudacao_e_data()
    with sessao() as (_, cur):
        cur.execute("""
            SELECT a.id, a.data_hora, p.nome AS pet, s.nome AS servico, s.preco
            FROM agendamentos a
            INNER JOIN pets p ON p.id = a.pet_id
            INNER JOIN servicos s ON s.id = a.servico_id
            WHERE p.cliente_id = %s AND a.status = 'Agendado' AND a.data_hora >= NOW()
            ORDER BY a.data_hora LIMIT 3
        """, (current_user.cliente_id,))
        proximos = cur.fetchall()
        cur.execute("SELECT id, nome, especie, raca FROM pets WHERE cliente_id = %s ORDER BY nome",
                    (current_user.cliente_id,))
        pets = cur.fetchall()
    return render_template("portal/painel.html", proximos=proximos, pets=pets,
                           saudacao=saudacao, hoje=hoje)


# ---------------------------------------------------------------- pets
def _ler_pet(form):
    """Valida o formulário do pet. Retorna (valores, erro)."""
    nome = form.get("nome", "").strip()
    especie = form.get("especie", "").strip()
    raca = form.get("raca", "").strip()
    nascimento = form.get("data_nascimento", "").strip()
    if not nome or len(nome) > 60:
        return None, "Informe o nome do pet (até 60 caracteres)."
    if especie not in ESPECIES:
        return None, "Escolha a espécie do pet."
    if len(raca) > 60:
        return None, "A raça deve ter até 60 caracteres."
    data_nasc = None
    if nascimento:
        try:
            data_nasc = datetime.strptime(nascimento, "%Y-%m-%d").date()
        except ValueError:
            return None, "Data de nascimento inválida."
        if data_nasc > date.today():
            return None, "A data de nascimento não pode estar no futuro."
    return {"nome": nome, "especie": especie, "raca": raca or None, "data_nascimento": data_nasc}, None


@bp.route("/pets")
def pets():
    with sessao() as (_, cur):
        cur.execute("""
            SELECT p.id, p.nome, p.especie, p.raca, p.data_nascimento,
                   (SELECT COUNT(*) FROM agendamentos a WHERE a.pet_id = p.id) AS total_agendamentos
            FROM pets p WHERE p.cliente_id = %s ORDER BY p.nome
        """, (current_user.cliente_id,))
        lista = cur.fetchall()
    return render_template("portal/pets.html", pets=lista)


@bp.route("/pets/novo", methods=["GET", "POST"])
def pet_novo():
    registro = {}
    if request.method == "POST":
        registro = request.form.to_dict()
        valores, erro = _ler_pet(request.form)
        if erro:
            flash(erro, "warning")
        else:
            with sessao() as (con, cur):
                cur.execute(
                    "INSERT INTO pets (nome, especie, raca, data_nascimento, cliente_id) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (valores["nome"], valores["especie"], valores["raca"],
                     valores["data_nascimento"], current_user.cliente_id))
                con.commit()
            flash(f"{valores['nome']} foi cadastrado!", "success")
            return redirect(url_for("portal.pets"))
    return render_template("portal/pet_form.html", registro=registro, especies=ESPECIES, editando=False,
                           hoje=date.today().isoformat())


@bp.route("/pets/<int:id>/editar", methods=["GET", "POST"])
def pet_editar(id):
    with sessao() as (con, cur):
        cur.execute("SELECT * FROM pets WHERE id = %s AND cliente_id = %s", (id, current_user.cliente_id))
        atual = cur.fetchone()
        if atual is None:
            abort(404)
        registro = {k: ("" if v is None else str(v)) for k, v in atual.items()}
        if request.method == "POST":
            registro = {**registro, **request.form.to_dict()}
            valores, erro = _ler_pet(request.form)
            if erro:
                flash(erro, "warning")
            else:
                cur.execute(
                    "UPDATE pets SET nome = %s, especie = %s, raca = %s, data_nascimento = %s "
                    "WHERE id = %s AND cliente_id = %s",
                    (valores["nome"], valores["especie"], valores["raca"], valores["data_nascimento"],
                     id, current_user.cliente_id))
                con.commit()
                flash("Dados do pet atualizados!", "success")
                return redirect(url_for("portal.pets"))
    return render_template("portal/pet_form.html", registro=registro, especies=ESPECIES, editando=True,
                           hoje=date.today().isoformat())


@bp.route("/pets/<int:id>/excluir", methods=["POST"])
def pet_excluir(id):
    with sessao() as (con, cur):
        try:
            cur.execute("DELETE FROM pets WHERE id = %s AND cliente_id = %s", (id, current_user.cliente_id))
            con.commit()
            if cur.rowcount:
                flash("Pet removido.", "success")
            else:
                abort(404)
        except mysql.connector.IntegrityError:
            con.rollback()
            flash("Este pet tem agendamentos no histórico e não pode ser removido.", "warning")
    return redirect(url_for("portal.pets"))


# ---------------------------------------------------------------- agendamentos
def _horarios():
    """Lista de horários oferecidos no formulário: 08:00, 08:30, ... até uma hora antes de fechar."""
    cfg = current_app.config
    atual = datetime(2000, 1, 1, cfg["HORA_ABERTURA"])
    limite = datetime(2000, 1, 1, cfg["HORA_FECHAMENTO"])
    saida = []
    while atual < limite:
        saida.append(atual.strftime("%H:%M"))
        atual += timedelta(minutes=cfg["INTERVALO_MIN"])
    return saida


def _montar_agendamento(cur, form):
    """Valida os dados do agendamento. Retorna (dados, erro). Todas as regras do negócio ficam aqui."""
    cfg = current_app.config
    try:
        pet_id = int(form.get("pet_id", ""))
        servico_id = int(form.get("servico_id", ""))
    except ValueError:
        return None, "Escolha o pet e o serviço."

    cur.execute("SELECT id FROM pets WHERE id = %s AND cliente_id = %s", (pet_id, current_user.cliente_id))
    if cur.fetchone() is None:
        return None, "Pet inválido."
    cur.execute("SELECT id, duracao_min FROM servicos WHERE id = %s", (servico_id,))
    servico = cur.fetchone()
    if servico is None:
        return None, "Serviço inválido."

    try:
        inicio = datetime.strptime(f"{form.get('data', '')} {form.get('hora', '')}", "%Y-%m-%d %H:%M")
    except ValueError:
        return None, "Escolha a data e o horário."
    if inicio <= datetime.now():
        return None, "Escolha um horário no futuro."
    if inicio > datetime.now() + timedelta(days=ANTECEDENCIA_MAX_DIAS):
        return None, f"Só é possível agendar com até {ANTECEDENCIA_MAX_DIAS} dias de antecedência."
    if inicio.weekday() not in cfg["DIAS_FUNCIONAMENTO"]:
        return None, "A loja não funciona nesse dia. Escolha outra data."
    if form.get("hora") not in _horarios():
        return None, "Escolha um dos horários da lista."
    fim = inicio + timedelta(minutes=servico["duracao_min"])
    if fim > inicio.replace(hour=cfg["HORA_FECHAMENTO"], minute=0):
        return None, "Esse serviço não termina antes do fechamento. Escolha um horário mais cedo."

    observacoes = form.get("observacoes", "").strip()
    if len(observacoes) > 200:
        return None, "As observações devem ter até 200 caracteres."

    # o mesmo pet não pode ter dois atendimentos ao mesmo tempo
    sobrepoe = ("a.status = 'Agendado' AND a.data_hora < %s "
                "AND DATE_ADD(a.data_hora, INTERVAL s.duracao_min MINUTE) > %s")
    cur.execute(f"SELECT COUNT(*) AS n FROM agendamentos a INNER JOIN servicos s ON s.id = a.servico_id "
                f"WHERE a.pet_id = %s AND {sobrepoe}", (pet_id, fim, inicio))
    if cur.fetchone()["n"]:
        return None, "Esse pet já tem um agendamento nesse horário."
    # capacidade da loja
    cur.execute(f"SELECT COUNT(*) AS n FROM agendamentos a INNER JOIN servicos s ON s.id = a.servico_id "
                f"WHERE {sobrepoe}", (fim, inicio))
    if cur.fetchone()["n"] >= cfg["ATENDIMENTOS_SIMULTANEOS"]:
        return None, "Esse horário já está lotado. Escolha outro."

    return dict(pet_id=pet_id, servico_id=servico_id, data_hora=inicio, observacoes=observacoes or None), None


@bp.route("/agendamentos")
def agendamentos():
    with sessao() as (_, cur):
        cur.execute("""
            SELECT a.id, a.data_hora, a.status, a.observacoes, p.nome AS pet, s.nome AS servico, s.preco
            FROM agendamentos a
            INNER JOIN pets p ON p.id = a.pet_id
            INNER JOIN servicos s ON s.id = a.servico_id
            WHERE p.cliente_id = %s
            ORDER BY a.data_hora DESC
        """, (current_user.cliente_id,))
        todos = cur.fetchall()
    agora = datetime.now()
    proximos = sorted((a for a in todos if a["status"] == "Agendado" and a["data_hora"] >= agora),
                      key=lambda a: a["data_hora"])
    historico = [a for a in todos if a not in proximos]
    return render_template("portal/agendamentos.html", proximos=proximos, historico=historico)


@bp.route("/agendamentos/novo", methods=["GET", "POST"])
def agendamento_novo():
    with sessao() as (con, cur):
        cur.execute("SELECT id, nome, especie FROM pets WHERE cliente_id = %s ORDER BY nome",
                    (current_user.cliente_id,))
        pets_cliente = cur.fetchall()
        if not pets_cliente:
            flash("Cadastre seu pet antes de agendar um horário.", "info")
            return redirect(url_for("portal.pet_novo"))
        cur.execute("SELECT id, nome, preco, duracao_min FROM servicos ORDER BY nome")
        servicos = cur.fetchall()

        registro = {"pet_id": request.args.get("pet", ""), "servico_id": request.args.get("servico", "")}
        if request.method == "POST":
            registro = request.form.to_dict()
            dados, erro = _montar_agendamento(cur, request.form)
            if erro:
                flash(erro, "warning")
            else:
                cur.execute(
                    "INSERT INTO agendamentos (pet_id, servico_id, data_hora, status, observacoes) "
                    "VALUES (%s, %s, %s, 'Agendado', %s)",
                    (dados["pet_id"], dados["servico_id"], dados["data_hora"], dados["observacoes"]))
                con.commit()
                flash("Agendamento confirmado! Te esperamos lá.", "success")
                return redirect(url_for("portal.agendamentos"))
    return render_template("portal/agendamento_form.html", registro=registro, pets=pets_cliente,
                           servicos=servicos, horarios=_horarios(), hoje=date.today().isoformat())


@bp.route("/agendamentos/<int:id>/cancelar", methods=["POST"])
def agendamento_cancelar(id):
    with sessao() as (con, cur):
        cur.execute("""
            UPDATE agendamentos a INNER JOIN pets p ON p.id = a.pet_id
            SET a.status = 'Cancelado'
            WHERE a.id = %s AND p.cliente_id = %s AND a.status = 'Agendado' AND a.data_hora > NOW()
        """, (id, current_user.cliente_id))
        con.commit()
        if cur.rowcount:
            flash("Agendamento cancelado.", "success")
        else:
            flash("Não foi possível cancelar este agendamento.", "warning")
    return redirect(url_for("portal.agendamentos"))


# ---------------------------------------------------------------- perfil
@bp.route("/perfil", methods=["GET", "POST"])
def perfil():
    with sessao() as (con, cur):
        cur.execute("SELECT id, nome, telefone, cidade FROM clientes WHERE id = %s", (current_user.cliente_id,))
        cliente = cur.fetchone()
        if cliente is None:
            abort(404)
        registro = {k: ("" if v is None else str(v)) for k, v in cliente.items()}
        if request.method == "POST":
            registro = {**registro, **{k: request.form.get(k, "").strip() for k in ("nome", "telefone", "cidade")}}
            atual, nova, confirmar = (request.form.get(k, "") for k in ("senha_atual", "nova_senha", "confirmar"))
            erro = None
            if not registro["nome"] or len(registro["nome"]) > 100:
                erro = "Informe seu nome (até 100 caracteres)."
            elif len(registro["telefone"]) > 20 or len(registro["cidade"]) > 60:
                erro = "Telefone (até 20) ou cidade (até 60 caracteres) muito longos."
            elif nova:
                cur.execute("SELECT senha_hash FROM usuarios WHERE id = %s", (current_user.get_id(),))
                if not check_password_hash(cur.fetchone()["senha_hash"], atual):
                    erro = "A senha atual está incorreta."
                elif len(nova) < 6:
                    erro = "A nova senha deve ter pelo menos 6 caracteres."
                elif nova != confirmar:
                    erro = "A confirmação da nova senha não confere."
            if erro:
                flash(erro, "warning")
            else:
                cur.execute("UPDATE clientes SET nome = %s, telefone = %s, cidade = %s WHERE id = %s",
                            (registro["nome"], registro["telefone"] or None, registro["cidade"] or None,
                             current_user.cliente_id))
                cur.execute("UPDATE usuarios SET nome = %s WHERE id = %s", (registro["nome"], current_user.get_id()))
                if nova:
                    cur.execute("UPDATE usuarios SET senha_hash = %s WHERE id = %s",
                                (generate_password_hash(nova), current_user.get_id()))
                con.commit()
                flash("Seus dados foram atualizados!", "success")
                return redirect(url_for("portal.perfil"))
    return render_template("portal/perfil.html", registro=registro)

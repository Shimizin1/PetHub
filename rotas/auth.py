import re

import mysql.connector
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from acesso import destino_do_perfil, caminho_interno
from database import sessao, SemConexao
from usuario import Usuario

bp = Blueprint("auth", __name__)

LOGIN_VALIDO = re.compile(r"[a-z0-9._-]{3,30}")


@bp.route("/painel")
def painel():
    """Leva cada perfil para a sua área: equipe -> /admin, cliente -> /cliente."""
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    destino = destino_do_perfil(current_user.perfil)
    if destino is None:                      # perfil desconhecido: não deixa entrar
        logout_user()
        flash("Seu usuário não tem um perfil válido. Fale com a loja.", "warning")
        return redirect(url_for("auth.login"))
    return redirect(url_for(destino))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("auth.painel"))
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "")
        try:
            with sessao() as (_, cur):
                cur.execute("SELECT id, nome, perfil, cliente_id, senha_hash FROM usuarios WHERE usuario = %s",
                            (usuario,))
                linha = cur.fetchone()
        except SemConexao:
            flash("Falha na conexão com o banco.", "danger")
            return render_template("auth/login.html")
        if linha and check_password_hash(linha["senha_hash"], senha):
            login_user(Usuario(linha["id"], linha["nome"], linha["perfil"], linha["cliente_id"]))
            destino = request.args.get("next", "")
            if caminho_interno(destino):
                return redirect(destino)
            return redirect(url_for("auth.painel"))
        flash("Usuário ou senha incorretos. Confira e tente de novo.", "danger")
    return render_template("auth/login.html")


@bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    flash("Você saiu do sistema.", "success")
    return redirect(url_for("publico.home"))


@bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    """Auto-cadastro do cliente: cria o dono (clientes) e o login (usuarios) numa transação só."""
    if current_user.is_authenticated:
        return redirect(url_for("auth.painel"))
    form = {}
    if request.method == "POST":
        form = {k: request.form.get(k, "").strip() for k in ("nome", "telefone", "cidade", "usuario")}
        form["usuario"] = form["usuario"].lower()
        senha = request.form.get("senha", "")
        confirmar = request.form.get("confirmar", "")

        erro = None
        if not form["nome"] or len(form["nome"]) > 100:
            erro = "Informe seu nome (até 100 caracteres)."
        elif len(form["telefone"]) > 20 or len(form["cidade"]) > 60:
            erro = "Telefone (até 20) ou cidade (até 60 caracteres) muito longos."
        elif not LOGIN_VALIDO.fullmatch(form["usuario"]):
            erro = "O usuário deve ter de 3 a 30 caracteres: letras minúsculas, números, ponto, hífen ou _."
        elif len(senha) < 6:
            erro = "A senha deve ter pelo menos 6 caracteres."
        elif senha != confirmar:
            erro = "As senhas não conferem."

        if erro:
            flash(erro, "warning")
        else:
            try:
                with sessao() as (con, cur):
                    try:
                        cur.execute("INSERT INTO clientes (nome, telefone, cidade) VALUES (%s, %s, %s)",
                                    (form["nome"], form["telefone"] or None, form["cidade"] or None))
                        cliente_id = cur.lastrowid
                        cur.execute(
                            "INSERT INTO usuarios (nome, usuario, senha_hash, perfil, cliente_id) "
                            "VALUES (%s, %s, %s, 'cliente', %s)",
                            (form["nome"], form["usuario"], generate_password_hash(senha), cliente_id))
                        con.commit()
                    except mysql.connector.IntegrityError:
                        con.rollback()
                        flash("Esse nome de usuário já está em uso. Escolha outro.", "warning")
                    except mysql.connector.Error:
                        con.rollback()
                        flash("Não foi possível concluir o cadastro. Tente novamente.", "danger")
                    else:
                        login_user(Usuario(cur.lastrowid, form["nome"], "cliente", cliente_id))
                        flash("Conta criada! Agora cadastre seu pet e agende um horário.", "success")
                        return redirect(url_for("portal.painel"))
            except SemConexao:
                flash("Falha na conexão com o banco.", "danger")
    return render_template("auth/cadastro.html", form=form)

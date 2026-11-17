from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import (LoginManager, UserMixin, login_user, logout_user,
                         current_user)
from werkzeug.security import check_password_hash

from config import Config
from database import get_connection
from modulos import TODOS, MENU
from permissoes import PERFIS, pode, nivel_nome

app = Flask(__name__)
app.config.from_object(Config)

for blueprint in TODOS:
    app.register_blueprint(blueprint)

# ---------- Login (Flask-Login) ----------
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Faça login para continuar."
login_manager.login_message_category = "warning"


class Usuario(UserMixin):
    def __init__(self, id, nome, perfil):
        self.id = str(id)
        self.nome = nome
        self.perfil = perfil


@login_manager.user_loader
def carregar_usuario(user_id):
    conexao = get_connection()
    if conexao is None:
        return None
    cursor = conexao.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, nome, perfil FROM usuarios WHERE id = %s", (user_id,))
        linha = cursor.fetchone()
        return Usuario(linha["id"], linha["nome"], linha["perfil"]) if linha else None
    finally:
        cursor.close()
        conexao.close()


@app.context_processor
def contexto_global():
    """Deixa disponíveis em todos os templates: menu, perfis e as funções pode()/nivel()."""
    def pode_(modulo, acao):
        return current_user.is_authenticated and pode(current_user.perfil, modulo, acao)

    def nivel_(modulo):
        return nivel_nome(current_user.perfil, modulo) if current_user.is_authenticated else "nenhum"

    return dict(pode=pode_, nivel=nivel_, PERFIS=PERFIS, MENU=MENU)


@app.before_request
def exigir_login():
    """Todas as telas exigem login, exceto a de login e os arquivos estáticos."""
    if request.endpoint in (None, "login", "static"):
        return None
    if not current_user.is_authenticated:
        return login_manager.unauthorized()
    return None


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "")
        conexao = get_connection()
        if conexao is None:
            flash("Falha na conexão com o banco.", "danger")
            return render_template("login.html")
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id, nome, perfil, senha_hash FROM usuarios WHERE usuario = %s",
                           (usuario,))
            linha = cursor.fetchone()
        finally:
            cursor.close()
            conexao.close()
        if linha and check_password_hash(linha["senha_hash"], senha):
            login_user(Usuario(linha["id"], linha["nome"], linha["perfil"]))
            destino = request.args.get("next", "")
            # só aceita redirecionar para caminhos internos do próprio site
            if destino.startswith("/") and not destino.startswith("//"):
                return redirect(destino)
            return redirect(url_for("dashboard"))
        flash("Usuário ou senha incorretos. Confira e tente de novo.", "danger")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    logout_user()
    flash("Você saiu do sistema.", "success")
    return redirect(url_for("login"))


# ---------- Dashboard ----------
@app.route("/")
def dashboard():
    agora = datetime.now()
    dias = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
            "sexta-feira", "sábado", "domingo"]
    meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
             "agosto", "setembro", "outubro", "novembro", "dezembro"]
    hoje = f"{dias[agora.weekday()]}, {agora.day} de {meses[agora.month - 1]}"
    saudacao = "Bom dia" if agora.hour < 12 else ("Boa tarde" if agora.hour < 18 else "Boa noite")
    vazio = dict(total_clientes=0, total_pets=0, total_pendentes=0,
                 faturamento=None, proximos=[], hoje=hoje, saudacao=saudacao)
    conexao = get_connection()
    if conexao is None:
        return render_template("dashboard.html", erro="Não foi possível conectar ao banco de dados.", **vazio)
    cursor = conexao.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) AS total FROM clientes")
        total_clientes = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM pets")
        total_pets = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM agendamentos WHERE status = 'Agendado'")
        total_pendentes = cursor.fetchone()["total"]
        faturamento = None            # só o administrador enxerga o financeiro
        if pode(current_user.perfil, "financeiro", "listar"):
            cursor.execute("""
                SELECT COALESCE(SUM(s.preco), 0) AS total
                FROM agendamentos a INNER JOIN servicos s ON s.id = a.servico_id
                WHERE a.status = 'Concluído'
            """)
            faturamento = cursor.fetchone()["total"]
        cursor.execute("""
            SELECT a.id, a.data_hora, p.nome AS pet, c.nome AS dono, s.nome AS servico
            FROM agendamentos a
            INNER JOIN pets p ON p.id = a.pet_id
            INNER JOIN clientes c ON c.id = p.cliente_id
            INNER JOIN servicos s ON s.id = a.servico_id
            WHERE a.status = 'Agendado'
            ORDER BY a.data_hora LIMIT 5
        """)
        proximos = cursor.fetchall()
        return render_template("dashboard.html", erro=None, total_clientes=total_clientes,
                               total_pets=total_pets, total_pendentes=total_pendentes,
                               faturamento=faturamento, proximos=proximos,
                               hoje=hoje, saudacao=saudacao)
    finally:
        cursor.close()
        conexao.close()


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"], host="127.0.0.1", port=5000)

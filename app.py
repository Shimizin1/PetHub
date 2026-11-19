from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, current_user, logout_user

from acesso import BLUEPRINTS_ABERTOS, destino_do_perfil
from config import Config
from database import SemConexao
from modulos import TODOS, MENU
from permissoes import PERFIS, pode, nivel_nome, eh_equipe, eh_cliente
from rotas import BLUEPRINTS
from usuario import carregar_por_id
from utilidades import moeda, data_br, datahora_br, status_classe

# Os arquivos estáticos ficam em public/static: a Vercel serve a pasta public/ pela CDN
# (o static_folder do Flask é ignorado lá) e, localmente, o Flask serve a mesma pasta.
app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config.from_object(Config)

# ---------- Rotas ----------
# publico (/), auth (/login, /cadastro), portal (/cliente) e admin (/admin) ...
for blueprint in BLUEPRINTS:
    app.register_blueprint(blueprint)
# ... e os CRUDs da equipe (/admin/clientes, /admin/pets, ...), montados em modulos.py
for blueprint in TODOS:
    app.register_blueprint(blueprint)

# ---------- Login (Flask-Login) ----------
login_manager = LoginManager(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "Faça login para continuar."
login_manager.login_message_category = "warning"
login_manager.user_loader(carregar_por_id)


@app.before_request
def proteger_areas():
    """
    Seguro por padrão: tudo é protegido, exceto os blueprints abertos (publico, auth) e os estáticos.
      - /cliente/*  -> só perfil cliente
      - o resto     -> só equipe (administrador, atendente, veterinário)
    A permissão por módulo (clientes, pets...) continua sendo checada em crud.py.
    """
    if request.endpoint in (None, "static") or request.blueprint in BLUEPRINTS_ABERTOS:
        return None
    if not current_user.is_authenticated:
        return login_manager.unauthorized()

    area_cliente = request.blueprint == "portal"
    perfil_ok = eh_cliente(current_user.perfil) if area_cliente else eh_equipe(current_user.perfil)
    if perfil_ok and area_cliente and not current_user.cliente_id:
        perfil_ok = False                       # login de cliente sem cadastro de dono ligado
    if perfil_ok:
        return None

    perfil_desconhecido = destino_do_perfil(current_user.perfil) is None
    cliente_sem_cadastro = area_cliente and eh_cliente(current_user.perfil)
    if perfil_desconhecido or cliente_sem_cadastro:
        logout_user()
        flash("Sua conta não está configurada corretamente. Fale com a loja.", "warning")
        return redirect(url_for("auth.login"))
    flash("Você não tem acesso a essa área.", "warning")
    return redirect(url_for("auth.painel"))


# ---------- Disponível em todos os templates ----------
app.jinja_env.filters.update(moeda=moeda, data_br=data_br, datahora_br=datahora_br,
                             status_classe=status_classe)


def layout_do_usuario():
    """Layout que combina com quem está navegando (usado nas telas de erro)."""
    if current_user.is_authenticated:
        if eh_equipe(current_user.perfil):
            return "layouts/admin.html"
        if eh_cliente(current_user.perfil):
            return "layouts/cliente.html"
    return "layouts/publico.html"


@app.context_processor
def contexto_global():
    def pode_(modulo, acao):
        return current_user.is_authenticated and pode(current_user.perfil, modulo, acao)

    def nivel_(modulo):
        return nivel_nome(current_user.perfil, modulo) if current_user.is_authenticated else "nenhum"

    cfg = app.config
    loja = dict(
        nome="PetHub",
        horario=f"Segunda a sábado, das {cfg['HORA_ABERTURA']}h às {cfg['HORA_FECHAMENTO']}h",
    )
    return dict(pode=pode_, nivel=nivel_, PERFIS=PERFIS, MENU=MENU, loja=loja)


# ---------- Telas de erro ----------
def _erro(codigo, titulo, mensagem):
    return render_template("erro.html", layout=layout_do_usuario(), codigo=codigo,
                           titulo=titulo, mensagem=mensagem), codigo


@app.errorhandler(404)
def pagina_nao_encontrada(_):
    return _erro(404, "Página não encontrada", "O endereço não existe ou o registro não é seu.")


@app.errorhandler(405)
def metodo_nao_permitido(_):
    return _erro(405, "Ação não permitida", "Essa ação não está disponível por este caminho.")


@app.errorhandler(SemConexao)
def banco_fora_do_ar(_):
    return _erro(503, "Sistema indisponível", "Não conseguimos falar com o banco de dados. Tente em instantes.")


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"], host="127.0.0.1", port=5000)

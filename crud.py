"""
Fábrica de CRUD: cria um Blueprint completo (listar, novo, editar, excluir)
a partir de uma descrição dos campos. Cada módulo do sistema (clientes, pets,
serviços, agendamentos, usuários) usa esta mesma lógica, mudando só a configuração
que está em modulos.py.
"""
from datetime import datetime, date
from decimal import Decimal, InvalidOperation

import mysql.connector
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from werkzeug.security import generate_password_hash

from database import get_connection
from permissoes import pode, nivel_nome


def _fixas(campo):
    """Opções fixas: aceita "Texto" ou ("valor_no_banco", "Texto na tela")."""
    return [(o, o) if isinstance(o, str) else o for o in campo["opcoes_fixas"]]


def _opcoes(campo, cursor):
    """Devolve a lista (valor, texto) das opções de um campo do tipo select."""
    if "opcoes_fixas" in campo:
        return _fixas(campo)
    cursor.execute(campo["opcoes_sql"])
    return [(linha["id"], linha["texto"]) for linha in cursor.fetchall()]


def _ler_formulario(campos, editando, parcial=False):
    """Valida o que veio do formulário. Retorna (valores, mensagem_de_erro)."""
    valores = {}
    for c in campos:
        if parcial and not c.get("parcial"):
            continue                      # perfil com edição parcial só altera campos marcados
        tipo = c["tipo"]
        nome_input = "senha" if tipo == "senha" else c["nome"]
        bruto = request.form.get(nome_input, "").strip()

        if tipo == "senha":
            if not bruto:
                if editando:          # na edição, senha em branco = manter a atual
                    continue
                return None, "Informe a senha."
            if len(bruto) < 6:
                return None, "A senha deve ter pelo menos 6 caracteres."
            valores[c["nome"]] = generate_password_hash(bruto)  # nunca salva texto puro
            continue

        if not bruto:
            if c.get("obrigatorio"):
                return None, f"Preencha o campo {c['rotulo']}."
            valores[c["nome"]] = None
            continue

        try:
            if tipo == "texto":
                if len(bruto) > c.get("max", 100):
                    return None, f"{c['rotulo']} deve ter até {c.get('max', 100)} caracteres."
                valores[c["nome"]] = bruto
            elif tipo == "decimal":
                numero = Decimal(bruto.replace(",", "."))
                if not numero.is_finite() or numero < 0 or numero > Decimal("99999999.99"):
                    return None, f"{c['rotulo']} inválido."
                valores[c["nome"]] = numero.quantize(Decimal("0.01"))
            elif tipo == "inteiro":
                numero = int(bruto)
                if numero < 0:
                    return None, f"{c['rotulo']} não pode ser negativo."
                valores[c["nome"]] = numero
            elif tipo == "data":
                valores[c["nome"]] = datetime.strptime(bruto, "%Y-%m-%d").date()
            elif tipo == "datahora":
                valores[c["nome"]] = datetime.strptime(bruto, "%Y-%m-%dT%H:%M")
            elif tipo == "select":
                if "opcoes_fixas" in c:
                    if bruto not in [v for v, _ in _fixas(c)]:
                        return None, f"{c['rotulo']} inválido."
                    valores[c["nome"]] = bruto
                else:
                    valores[c["nome"]] = int(bruto)
        except (InvalidOperation, ValueError):
            return None, f"{c['rotulo']} inválido."
    return valores, None


def _para_formulario(registro):
    """Converte os valores vindos do MySQL em texto aceito pelos <input> HTML."""
    saida = {}
    for chave, valor in registro.items():
        if valor is None:
            saida[chave] = ""
        elif isinstance(valor, datetime):
            saida[chave] = valor.strftime("%Y-%m-%dT%H:%M")
        elif isinstance(valor, date):
            saida[chave] = valor.isoformat()
        else:
            saida[chave] = str(valor)
    return saida


def criar_crud(endpoint, titulo, tabela, campos, sql_listagem, colunas,
               busca_sql, ordem, descricao="", bloquear_proprio=False):
    bp = Blueprint(endpoint, __name__, url_prefix=f"/{endpoint}")
    ctx = dict(endpoint=endpoint, titulo=titulo, campos=campos, descricao=descricao)

    @bp.before_request
    def checar_permissao():
        """Barra quem não tem permissão para a ação (listar, novo, editar, excluir)."""
        acao = request.endpoint.split(".")[1]
        if not pode(current_user.perfil, endpoint, acao):
            flash("Seu perfil não tem acesso a esta área.", "warning")
            return redirect(url_for("dashboard"))

    @bp.route("/")
    def listar():
        busca = request.args.get("busca", "").strip()
        conexao = get_connection()
        if conexao is None:
            flash("Falha na conexão com o banco.", "danger")
            return render_template("listar.html", registros=[], busca=busca,
                                   colunas=colunas, **ctx)
        cursor = conexao.cursor(dictionary=True)
        try:
            if busca:
                filtro = " WHERE " + " OR ".join(f"{e} LIKE %s" for e in busca_sql)
                parametros = tuple([f"%{busca}%"] * len(busca_sql))
            else:
                filtro, parametros = "", ()
            cursor.execute(f"{sql_listagem}{filtro} ORDER BY {ordem}", parametros)
            return render_template("listar.html", registros=cursor.fetchall(),
                                   busca=busca, colunas=colunas, **ctx)
        finally:
            cursor.close()
            conexao.close()

    @bp.route("/novo", methods=["GET", "POST"])
    def novo():
        conexao = get_connection()
        if conexao is None:
            flash("Falha na conexão com o banco.", "danger")
            return redirect(url_for(f"{endpoint}.listar"))
        cursor = conexao.cursor(dictionary=True)
        try:
            opcoes = {c["nome"]: _opcoes(c, cursor) for c in campos if c["tipo"] == "select"}
            registro = {}
            if request.method == "POST":
                registro = request.form.to_dict()
                valores, erro = _ler_formulario(campos, editando=False)
                if erro:
                    flash(erro, "warning")
                else:
                    try:
                        colunas_sql = ", ".join(valores)
                        marcadores = ", ".join(["%s"] * len(valores))
                        cursor.execute(
                            f"INSERT INTO {tabela} ({colunas_sql}) VALUES ({marcadores})",
                            tuple(valores.values()))
                        conexao.commit()
                        flash("Cadastro realizado com sucesso!", "success")
                        return redirect(url_for(f"{endpoint}.listar"))
                    except mysql.connector.Error:
                        conexao.rollback()
                        flash("Não foi possível salvar (verifique se o dado já existe).", "danger")
            return render_template("formulario.html", registro=registro,
                                   opcoes=opcoes, editando=False, parcial=False, **ctx)
        finally:
            cursor.close()
            conexao.close()

    @bp.route("/editar/<int:id>", methods=["GET", "POST"])
    def editar(id):
        conexao = get_connection()
        if conexao is None:
            flash("Falha na conexão com o banco.", "danger")
            return redirect(url_for(f"{endpoint}.listar"))
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(f"SELECT * FROM {tabela} WHERE id = %s", (id,))
            atual = cursor.fetchone()
            if atual is None:
                flash("Registro não encontrado.", "warning")
                return redirect(url_for(f"{endpoint}.listar"))
            opcoes = {c["nome"]: _opcoes(c, cursor) for c in campos if c["tipo"] == "select"}
            registro = _para_formulario(atual)
            parcial = nivel_nome(current_user.perfil, endpoint) == "parcial"
            if request.method == "POST":
                registro = {**registro, **request.form.to_dict()}
                valores, erro = _ler_formulario(campos, editando=True, parcial=parcial)
                if erro:
                    flash(erro, "warning")
                else:
                    try:
                        sets = ", ".join(f"{col} = %s" for col in valores)
                        cursor.execute(f"UPDATE {tabela} SET {sets} WHERE id = %s",
                                       (*valores.values(), id))
                        conexao.commit()
                        flash("Registro atualizado com sucesso!", "success")
                        return redirect(url_for(f"{endpoint}.listar"))
                    except mysql.connector.Error:
                        conexao.rollback()
                        flash("Não foi possível atualizar (verifique se o dado já existe).", "danger")
            return render_template("formulario.html", registro=registro, opcoes=opcoes,
                                   editando=True, parcial=parcial, **ctx)
        finally:
            cursor.close()
            conexao.close()

    @bp.route("/excluir/<int:id>", methods=["POST"])
    def excluir(id):
        if bloquear_proprio and str(id) == str(current_user.get_id()):
            flash("Você não pode excluir o usuário que está logado.", "warning")
            return redirect(url_for(f"{endpoint}.listar"))
        conexao = get_connection()
        if conexao is None:
            flash("Falha na conexão com o banco.", "danger")
            return redirect(url_for(f"{endpoint}.listar"))
        cursor = conexao.cursor()
        try:
            cursor.execute(f"DELETE FROM {tabela} WHERE id = %s", (id,))
            conexao.commit()
            flash("Registro excluído com sucesso!", "success")
        except mysql.connector.IntegrityError:
            conexao.rollback()
            flash("Este registro possui vínculos com outros cadastros e não pode ser excluído.", "warning")
        except mysql.connector.Error:
            conexao.rollback()
            flash("Não foi possível excluir o registro.", "danger")
        finally:
            cursor.close()
            conexao.close()
        return redirect(url_for(f"{endpoint}.listar"))

    return bp

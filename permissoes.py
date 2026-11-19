"""
Controle de acesso por perfil.

Há dois "mundos" no sistema:
  - EQUIPE  (administrador, atendente, veterinário) -> área /admin
  - CLIENTE (dono do pet)                           -> área /cliente

Níveis de permissão de um perfil da equipe em cada módulo do /admin:
  nenhum  -> não vê o módulo
  leitura -> só consulta (listar)
  parcial -> consulta e altera apenas os campos marcados com "parcial": True em modulos.py
  total   -> consulta, cadastra, edita e exclui

O cliente não aparece em PERMISSOES de propósito: ele nunca acessa os módulos do /admin.
Já o que ele pode fazer na própria área (ver só os SEUS pets e agendamentos) é garantido
em rotas/portal.py, filtrando sempre pelo cliente_id do usuário logado.
"""

PERFIS = {
    "administrador": "Administrador",
    "atendente": "Atendente",
    "veterinario": "Veterinário",
    "cliente": "Cliente",
}

PERFIS_EQUIPE = ("administrador", "atendente", "veterinario")
PERFIL_CLIENTE = "cliente"

PERMISSOES = {
    "administrador": {
        "clientes": "total", "pets": "total", "servicos": "total",
        "agendamentos": "total", "usuarios": "total", "financeiro": "leitura",
    },
    "atendente": {
        "clientes": "total", "pets": "total", "servicos": "leitura",
        "agendamentos": "total",
    },
    "veterinario": {
        "pets": "leitura", "servicos": "leitura", "agendamentos": "parcial",
    },
}

NIVEIS = {"nenhum": 0, "leitura": 1, "parcial": 2, "total": 3}
# nível mínimo exigido para cada ação
ACAO_MINIMA = {"listar": 1, "editar": 2, "novo": 3, "excluir": 3}


def nivel_nome(perfil, modulo):
    return PERMISSOES.get(perfil, {}).get(modulo, "nenhum")


def pode(perfil, modulo, acao):
    return NIVEIS[nivel_nome(perfil, modulo)] >= ACAO_MINIMA[acao]


def eh_equipe(perfil):
    return perfil in PERFIS_EQUIPE


def eh_cliente(perfil):
    return perfil == PERFIL_CLIENTE

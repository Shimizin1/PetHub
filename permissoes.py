"""
Controle de acesso por perfil.

Níveis de permissão de um perfil em cada módulo:
  nenhum  -> não vê o módulo
  leitura -> só consulta (listar)
  parcial -> consulta e altera apenas os campos marcados com "parcial": True em modulos.py
  total   -> consulta, cadastra, edita e exclui
"""

PERFIS = {
    "administrador": "Administrador",
    "atendente": "Atendente",
    "veterinario": "Veterinário",
}

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

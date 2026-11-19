"""Regras de acesso compartilhadas: para onde cada perfil vai e o que é rota aberta."""
from permissoes import eh_equipe, eh_cliente

# Blueprints que qualquer visitante (sem login) pode abrir
BLUEPRINTS_ABERTOS = {"publico", "auth"}


def destino_do_perfil(perfil):
    """Endpoint inicial de cada perfil depois do login. None = perfil desconhecido."""
    if eh_equipe(perfil):
        return "admin.dashboard"
    if eh_cliente(perfil):
        return "portal.painel"
    return None


def caminho_interno(destino):
    """Só aceita redirecionar para caminhos do próprio site (evita open redirect)."""
    return bool(destino) and destino.startswith("/") and not destino.startswith("//") and "\\" not in destino

from datetime import datetime

DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
        "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]


def saudacao_e_data():
    """Devolve ('Bom dia', 'terça-feira, 18 de novembro') para os painéis."""
    agora = datetime.now()
    hoje = f"{DIAS[agora.weekday()]}, {agora.day} de {MESES[agora.month - 1]}"
    saudacao = "Bom dia" if agora.hour < 12 else ("Boa tarde" if agora.hour < 18 else "Boa noite")
    return saudacao, hoje


def moeda(valor):
    """Filtro Jinja: 50 -> 'R$ 50,00'."""
    if valor is None:
        return "—"
    return "R$ " + f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def data_br(valor):
    return valor.strftime("%d/%m/%Y") if valor else "—"


def datahora_br(valor):
    return valor.strftime("%d/%m/%Y às %H:%M") if valor else "—"


def status_classe(status):
    """'Concluído' -> 'concluido' (classe CSS do chip de status)."""
    return (status or "").lower().replace("í", "i")

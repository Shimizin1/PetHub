import os

# Localmente o .env é carregado se o python-dotenv estiver instalado; na Vercel as
# variáveis vêm do painel do projeto e este bloco simplesmente não faz nada.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "chave-dev-local")

    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "pethub")

    # aceita DEBUG ou FLASK_DEBUG (o .env de vocês usa FLASK_DEBUG)
    DEBUG = os.getenv("DEBUG", os.getenv("FLASK_DEBUG", "False")).lower() == "true"

    # ---- Funcionamento da loja (usado no agendamento online do cliente) ----
    HORA_ABERTURA = 8                 # primeiro horário: 08:00
    HORA_FECHAMENTO = 18              # a loja fecha às 18:00
    INTERVALO_MIN = 30                # de quanto em quanto tempo há horários
    DIAS_FUNCIONAMENTO = (0, 1, 2, 3, 4, 5)   # 0=segunda ... 5=sábado (domingo fechado)
    ATENDIMENTOS_SIMULTANEOS = 2      # quantos pets a loja atende ao mesmo tempo
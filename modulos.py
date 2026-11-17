"""Configuração dos 5 cadastros do PetHub. Cada um vira um CRUD completo."""
from crud import criar_crud

ESPECIES = ["Cachorro", "Gato", "Ave", "Roedor", "Outro"]
STATUS = ["Agendado", "Concluído", "Cancelado"]
PERFIS_OPCOES = [("administrador", "Administrador"), ("atendente", "Atendente"),
                 ("veterinario", "Veterinário")]

# Itens do menu lateral: (módulo, texto, ícone do Bootstrap Icons)
MENU = [
    ("clientes", "Clientes", "bi-people"),
    ("pets", "Pets", "bi-balloon-heart"),
    ("servicos", "Serviços", "bi-scissors"),
    ("agendamentos", "Agendamentos", "bi-calendar-check"),
    ("usuarios", "Usuários", "bi-shield-lock"),
]

clientes_bp = criar_crud(
    endpoint="clientes", titulo="Clientes", tabela="clientes",
    descricao="Donos dos pets atendidos pela loja.",
    campos=[
        {"nome": "nome", "rotulo": "Nome", "tipo": "texto", "max": 100, "obrigatorio": True},
        {"nome": "telefone", "rotulo": "Telefone", "tipo": "texto", "max": 20},
        {"nome": "cidade", "rotulo": "Cidade", "tipo": "texto", "max": 60},
    ],
    sql_listagem="SELECT id, nome, telefone, cidade FROM clientes",
    colunas=[("ID", "id"), ("Nome", "nome"), ("Telefone", "telefone"), ("Cidade", "cidade")],
    busca_sql=["nome", "telefone", "cidade"], ordem="id DESC",
)

pets_bp = criar_crud(
    endpoint="pets", titulo="Pets", tabela="pets",
    descricao="Os bichinhos cadastrados e seus donos.",
    campos=[
        {"nome": "nome", "rotulo": "Nome do pet", "tipo": "texto", "max": 60, "obrigatorio": True},
        {"nome": "especie", "rotulo": "Espécie", "tipo": "select", "opcoes_fixas": ESPECIES, "obrigatorio": True},
        {"nome": "raca", "rotulo": "Raça", "tipo": "texto", "max": 60},
        {"nome": "data_nascimento", "rotulo": "Data de nascimento", "tipo": "data"},
        {"nome": "cliente_id", "rotulo": "Dono (cliente)", "tipo": "select", "obrigatorio": True,
         "opcoes_sql": "SELECT id, nome AS texto FROM clientes ORDER BY nome"},
    ],
    # JOIN: traz o nome do dono da tabela clientes
    sql_listagem=("SELECT p.id, p.nome, p.especie, p.raca, p.data_nascimento, c.nome AS dono "
                  "FROM pets p INNER JOIN clientes c ON c.id = p.cliente_id"),
    colunas=[("ID", "id"), ("Pet", "nome"), ("Espécie", "especie"), ("Raça", "raca"),
             ("Nascimento", "data_nascimento", "data"), ("Dono", "dono")],
    busca_sql=["p.nome", "p.especie", "p.raca", "c.nome"], ordem="p.id DESC",
)

servicos_bp = criar_crud(
    endpoint="servicos", titulo="Serviços", tabela="servicos",
    descricao="Banho, tosa, consultas e vacinas, com preço e duração.",
    campos=[
        {"nome": "nome", "rotulo": "Nome do serviço", "tipo": "texto", "max": 80, "obrigatorio": True},
        {"nome": "preco", "rotulo": "Preço (R$)", "tipo": "decimal", "obrigatorio": True},
        {"nome": "duracao_min", "rotulo": "Duração (minutos)", "tipo": "inteiro", "obrigatorio": True},
    ],
    sql_listagem="SELECT id, nome, preco, duracao_min FROM servicos",
    colunas=[("ID", "id"), ("Serviço", "nome"), ("Preço", "preco", "moeda"),
             ("Duração (min)", "duracao_min")],
    busca_sql=["nome"], ordem="id DESC",
)

agendamentos_bp = criar_crud(
    endpoint="agendamentos", titulo="Agendamentos", tabela="agendamentos",
    descricao="A agenda da loja: quem vem, quando e para qual serviço.",
    campos=[
        {"nome": "pet_id", "rotulo": "Pet", "tipo": "select", "obrigatorio": True,
         "opcoes_sql": ("SELECT p.id, CONCAT(p.nome, ' (', c.nome, ')') AS texto FROM pets p "
                        "INNER JOIN clientes c ON c.id = p.cliente_id ORDER BY p.nome")},
        {"nome": "servico_id", "rotulo": "Serviço", "tipo": "select", "obrigatorio": True,
         "opcoes_sql": "SELECT id, nome AS texto FROM servicos ORDER BY nome"},
        {"nome": "data_hora", "rotulo": "Data e hora", "tipo": "datahora", "obrigatorio": True},
        {"nome": "status", "rotulo": "Status", "tipo": "select", "opcoes_fixas": STATUS,
         "obrigatorio": True, "parcial": True},
        {"nome": "observacoes", "rotulo": "Observações", "tipo": "texto", "max": 200, "parcial": True},
    ],
    # JOIN em 4 tabelas: agendamentos + pets + clientes + servicos
    sql_listagem=("SELECT a.id, a.data_hora, p.nome AS pet, c.nome AS dono, "
                  "s.nome AS servico, s.preco, a.status "
                  "FROM agendamentos a "
                  "INNER JOIN pets p ON p.id = a.pet_id "
                  "INNER JOIN clientes c ON c.id = p.cliente_id "
                  "INNER JOIN servicos s ON s.id = a.servico_id"),
    colunas=[("ID", "id"), ("Data/hora", "data_hora", "datahora"), ("Pet", "pet"),
             ("Dono", "dono"), ("Serviço", "servico"), ("Valor", "preco", "moeda"),
             ("Status", "status", "status")],
    busca_sql=["p.nome", "c.nome", "s.nome", "a.status"], ordem="a.data_hora DESC",
)

usuarios_bp = criar_crud(
    endpoint="usuarios", titulo="Usuários", tabela="usuarios",
    descricao="Quem acessa o sistema e o que cada perfil pode fazer.",
    campos=[
        {"nome": "nome", "rotulo": "Nome", "tipo": "texto", "max": 100, "obrigatorio": True},
        {"nome": "usuario", "rotulo": "Usuário (login)", "tipo": "texto", "max": 30, "obrigatorio": True},
        {"nome": "perfil", "rotulo": "Perfil", "tipo": "select", "opcoes_fixas": PERFIS_OPCOES,
         "obrigatorio": True},
        {"nome": "senha_hash", "rotulo": "Senha", "tipo": "senha"},
    ],
    sql_listagem="SELECT id, nome, usuario, perfil FROM usuarios",
    colunas=[("ID", "id"), ("Nome", "nome"), ("Usuário", "usuario"), ("Perfil", "perfil", "perfil")],
    busca_sql=["nome", "usuario"], ordem="id DESC", bloquear_proprio=True,
)

TODOS = [clientes_bp, pets_bp, servicos_bp, agendamentos_bp, usuarios_bp]

# PetHub — Aplicação web com banco de dados (Flask + MySQL)

Trabalho em dupla — Shimi e Rafael Rodrigues. Apresentação: 19/11/2026 (10 min).

## 0. Logins de teste e perfis

| Perfil | Usuário / senha | O que pode fazer |
|---|---|---|
| Administrador | `admin` / `admin123` | Tudo: clientes, pets, serviços, agendamentos, usuários e o financeiro do início |
| Atendente | `atendente` / `atendente123` | Clientes, pets e agendamentos completos; serviços só consulta; sem acesso a usuários e financeiro |
| Veterinário | `veterinario` / `veterinario123` | Consulta pets e serviços; na agenda só atualiza status e observações |

As regras ficam em `permissoes.py` e são aplicadas no servidor (`crud.py`), não só escondendo botões.

## 1. Rodar o projeto (no Windows; no Linux use `python3`, `source venv/bin/activate`)

1. **Instale o MySQL Server 8 + Workbench e o Python** (se ainda não tiver). No instalador do Python, marque *Add to PATH*.
2. **Crie o banco:** abra o MySQL Workbench, conecte no servidor, `File > Open SQL Script...`, escolha `sql/petshop.sql` e clique no raio (executa tudo). Isso cria o banco `petshop`, as 5 tabelas e os dados de teste.
3. **Configure a senha do MySQL:** abra o arquivo `.env` e troque `sua_senha_mysql` pela senha do seu MySQL.
4. **Abra a pasta no VS Code e, no terminal, rode:**

```powershell
py -m venv venv
```
Cria um ambiente virtual (pasta `venv`): uma "caixinha" só deste projeto, para as bibliotecas não bagunçarem o Python do computador.

```powershell
.\venv\Scripts\Activate.ps1
```
Ativa o ambiente virtual (aparece `(venv)` no começo da linha). Se o PowerShell bloquear, rode antes `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, que libera scripts só nessa janela.

```powershell
pip install -r requirements.txt
```
Instala tudo que está listado no `requirements.txt` (Flask, conector do MySQL, python-dotenv e Flask-Login).

```powershell
python app.py
```
Inicia o servidor Flask. Acesse http://127.0.0.1:5000/ — login: **admin** / senha: **admin123**.

## 2. Estrutura

```
PetHub/
├── app.py          -> app Flask, login/logout e dashboard
├── permissoes.py   -> perfis e níveis de permissão (administrador, atendente, veterinário)
├── crud.py         -> "fábrica" de CRUD (listar, novo, editar, excluir) usada por todos os cadastros
├── modulos.py      -> configuração dos 5 cadastros (campos, JOINs, busca)
├── config.py / database.py / .env
├── sql/petshop.sql -> CREATE DATABASE, CREATE TABLE, INSERT, SELECT/JOIN
├── docs/           -> DER.md (diagrama) e ROTEIRO.md (divisão e apresentação)
├── templates/      -> base, login, dashboard, listar, formulario (Jinja2 + Bootstrap)
└── static/         -> css e js
```

## 3. Como o código funciona (para explicar na apresentação)

- **Banco:** 5 tabelas — `usuarios`, `clientes`, `pets`, `servicos`, `agendamentos`. Relações 1:N por chave estrangeira: cliente→pets, pet→agendamentos, serviço→agendamentos.
- **`database.py`:** `get_connection()` abre a conexão com o MySQL usando os dados do `.env`.
- **`crud.py`:** `criar_crud(...)` recebe a descrição de uma tabela e devolve um Blueprint com 4 rotas: `listar` (SELECT, com pesquisa `LIKE`), `novo` (INSERT), `editar` (UPDATE) e `excluir` (DELETE). Todas as consultas usam `%s` (parametrizadas), o que evita SQL Injection. Se tentar excluir algo com vínculo (ex.: cliente com pets), a chave estrangeira bloqueia e o sistema mostra aviso.
- **`modulos.py`:** só descreve cada cadastro. Os **JOINs** estão em `pets` (pets + clientes) e `agendamentos` (4 tabelas).
- **Login:** a senha é guardada como *hash* (`generate_password_hash`), nunca em texto puro. O `before_request` em `app.py` bloqueia qualquer página para quem não está logado.
- **Templates:** `listar.html` e `formulario.html` são genéricos e se montam a partir da configuração; `base.html` tem o menu.

## 4. Checklist do que o professor pediu

- [x] Banco com nome da empresa (`petshop`), 3 a 5 tabelas (são 5), PK em todas, FKs, tipos adequados
- [x] Mínimo de 5 registros nas tabelas principais (já inseridos)
- [x] Tela inicial (dashboard), menu, cadastro, listagem, pesquisa, edição, exclusão
- [x] Cadastro de usuários com usuário e senha (+ login)
- [x] CREATE DATABASE, CREATE TABLE, INSERT, SELECT, UPDATE, DELETE e JOIN
- [x] Script SQL (`sql/petshop.sql`) e modelo lógico (`docs/DER.md`)
- [ ] Apresentação (roteiro em `docs/ROTEIRO.md`)

## 5. Problemas comuns

- `Access denied for user`: senha errada no `.env`.
- `Can't connect to MySQL server`: o serviço do MySQL não está rodando (Windows: Serviços > MySQL80 > Iniciar).
- `ModuleNotFoundError`: o ambiente virtual não está ativado ou faltou o `pip install -r requirements.txt`.
- Esqueceu a senha do admin: no Workbench, apague o usuário e rode de novo só o INSERT de `usuarios` do script, ou cadastre outro em *Usuários* depois de logar.

# Roteiro da dupla — Shimi + Rafael (apresentação 19/11/2026)

## Divisão sugerida (os dois precisam saber explicar tudo, então troquem informações)

| Parte | Quem lidera | O outro faz |
|---|---|---|
| Banco: rodar `petshop.sql`, conferir tabelas e dados no Workbench | Rafael | Shimi confere e testa |
| Gerar o DER no Workbench (Reverse Engineer) e salvar imagem | Rafael | Shimi revisa |
| Rodar o sistema, testar login e cada CRUD | Shimi | Rafael testa também, anota bugs |
| Ler `crud.py`/`app.py` e explicar o código | os dois leem, cada um prepara metade | |
| Slides curtos (se a turma pedir) | Rafael | Shimi revisa |

## Cronograma até 19/11

- **05–07/11:** os dois rodam o projeto no computador e entendem o `petshop.sql`.
- **08–12/11:** personalizar (nome da loja, cores, algo extra que vocês queiram) e testar tudo (cadastrar, pesquisar, editar, excluir, tentar excluir cliente com pet).
- **13–16/11:** gerar o DER, ensaiar a apresentação cronometrada.
- **17–18/11:** ensaio final com o sistema aberto; backup: print das telas e o `.sql` no pen drive/nuvem.

## Apresentação — 10 minutos

1. **(1 min)** Problema: petshop precisa controlar clientes, pets, serviços e agenda (hoje em caderno/WhatsApp).
2. **(1 min)** Empresa sorteada: PetHub.
3. **(2 min)** Tabelas e relacionamentos: mostrar o DER; 1 cliente → vários pets → vários agendamentos; serviço ligado ao agendamento; `usuarios` para o login.
4. **(1 min)** Mostrar no Workbench: `CREATE TABLE`, `INSERT` e o `SELECT` com `JOIN`.
5. **(3 min)** Demo ao vivo: login → dashboard → cadastrar cliente → cadastrar pet desse cliente → criar agendamento → pesquisar → editar status para Concluído → excluir um registro → tentar excluir cliente com pet (mostrar o bloqueio da chave estrangeira).
6. **(2 min)** Como o app conversa com o banco: `.env` → `config.py` → `database.py` → consultas com `%s` em `crud.py`; senha com hash.

## Perguntas que o professor pode fazer

- *Por que usar chave estrangeira?* Garante integridade: não existe pet sem dono nem agendamento sem pet.
- *O que é o JOIN que vocês usaram?* `INNER JOIN` junta linhas de tabelas relacionadas pelo `id`/FK (ex.: agendamento + pet + cliente + serviço).
- *Como evitam SQL Injection?* Consultas parametrizadas (`%s`).
- *Como a senha é guardada?* Hash com salt (Werkzeug), nunca texto puro.
- *Onde ficam os dados?* No MySQL, não no código.

## Perfis (mostrar na demo)

Entre como `admin`, depois como `veterinario`: o menu muda, o financeiro some e a agenda só deixa atualizar status. Explique que a regra é checada no servidor (`permissoes.py` + `crud.py`).

## Dica

Evitem decorar: abram o código uma vez cada um e expliquem com as palavras de vocês. O professor vai perguntar a cada integrante.

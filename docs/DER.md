# Modelo lógico / DER — PetHub

Diagrama em Mermaid (cole em https://mermaid.live para gerar a imagem) — ou gere o diagrama oficial no
MySQL Workbench: menu **Database > Reverse Engineer...** → escolha o banco `petshop` → finalize.
O Workbench monta o EER automaticamente com as chaves estrangeiras.

```mermaid
erDiagram
    CLIENTES ||--o| USUARIOS : "tem login"
    CLIENTES ||--o{ PETS : "possui"
    PETS ||--o{ AGENDAMENTOS : "recebe"
    SERVICOS ||--o{ AGENDAMENTOS : "é realizado em"

    USUARIOS {
        int id PK
        varchar nome
        varchar usuario "UNIQUE"
        varchar senha_hash
        enum perfil "administrador|atendente|veterinario|cliente"
        int cliente_id FK "UNIQUE, só para perfil cliente"
    }
    CLIENTES {
        int id PK
        varchar nome
        varchar telefone
        varchar cidade
    }
    PETS {
        int id PK
        varchar nome
        varchar especie
        varchar raca
        date data_nascimento
        int cliente_id FK
    }
    SERVICOS {
        int id PK
        varchar nome
        decimal preco
        int duracao_min
    }
    AGENDAMENTOS {
        int id PK
        int pet_id FK
        int servico_id FK
        datetime data_hora
        varchar status
        varchar observacoes
    }
```

**Relacionamentos (1:N):** um cliente tem vários pets; um pet tem vários agendamentos; um serviço aparece em vários agendamentos.
`usuarios` guarda o login de todos. Contas de **cliente** ligam-se a um dono pela FK `cliente_id` (1:1); contas da equipe têm `cliente_id` nulo.

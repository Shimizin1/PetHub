-- =====================================================
-- PETSHOP - Script de criação do banco, tabelas e dados
-- =====================================================
CREATE DATABASE IF NOT EXISTS petshop
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE petshop;

CREATE TABLE clientes (
  id INT PRIMARY KEY AUTO_INCREMENT,
  nome VARCHAR(100) NOT NULL,
  telefone VARCHAR(20),
  cidade VARCHAR(60)
);

-- usuarios guarda o login de TODO mundo: equipe (administrador, atendente, veterinario)
-- e clientes. O cliente se liga ao seu cadastro de dono pela coluna cliente_id.
CREATE TABLE usuarios (
  id INT PRIMARY KEY AUTO_INCREMENT,
  nome VARCHAR(100) NOT NULL,
  usuario VARCHAR(30) NOT NULL UNIQUE,
  senha_hash VARCHAR(255) NOT NULL,
  perfil ENUM('administrador','atendente','veterinario','cliente') NOT NULL DEFAULT 'cliente',
  cliente_id INT NULL UNIQUE,
  CONSTRAINT fk_usuarios_clientes
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
);

CREATE TABLE pets (
  id INT PRIMARY KEY AUTO_INCREMENT,
  nome VARCHAR(60) NOT NULL,
  especie VARCHAR(30) NOT NULL,
  raca VARCHAR(60),
  data_nascimento DATE,
  cliente_id INT NOT NULL,
  CONSTRAINT fk_pets_clientes
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

CREATE TABLE servicos (
  id INT PRIMARY KEY AUTO_INCREMENT,
  nome VARCHAR(80) NOT NULL,
  preco DECIMAL(10,2) NOT NULL,
  duracao_min INT NOT NULL
);

CREATE TABLE agendamentos (
  id INT PRIMARY KEY AUTO_INCREMENT,
  pet_id INT NOT NULL,
  servico_id INT NOT NULL,
  data_hora DATETIME NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'Agendado',
  observacoes VARCHAR(200),
  CONSTRAINT fk_agend_pets
    FOREIGN KEY (pet_id) REFERENCES pets(id),
  CONSTRAINT fk_agend_servicos
    FOREIGN KEY (servico_id) REFERENCES servicos(id)
);

-- ---------- DADOS DE TESTE ----------
INSERT INTO clientes (nome, telefone, cidade) VALUES
('Ana Souza', '(63) 99111-1111', 'Palmas'),
('Bruno Lima', '(63) 99222-2222', 'Palmas'),
('Carla Mendes', '(63) 99333-3333', 'Gurupi'),
('Daniel Alves', '(63) 99444-4444', 'Paraíso do Tocantins'),
('Eva Costa', '(63) 99555-5555', 'Porto Nacional');

-- Logins de teste (as senhas ficam em hash, nunca em texto puro):
--   admin / admin123 · atendente / atendente123 · veterinario / veterinario123
--   ana / ana123  (CLIENTE, ligada ao cadastro "Ana Souza")
INSERT INTO usuarios (nome, usuario, senha_hash, perfil, cliente_id) VALUES
('Administrador', 'admin', 'scrypt:32768:8:1$cdBGfXNvglGhcxQZ$1f6450daee52b5fdb972e110dfc8d96ffeefb18a3d5c791f971219525d50d8303e9b964162752a0808f5565d8ec09c79bfc2994348f8ddc67725f7a9dd2ccb50', 'administrador', NULL),
('Atendente', 'atendente', 'scrypt:32768:8:1$d5G8BEf4LAH3cyXk$e48201dcfd3a53ac16ef6e83438073843e9116373145fa770439255fa514aac706fe81373dc2c013197842ca96c9251a6439edf38920f62304e6f7a5aa24f4b3', 'atendente', NULL),
('Veterinário', 'veterinario', 'scrypt:32768:8:1$WHyLlhvegqs1wAIu$d8593718177dc4683ff78e39641841fe05dc6176d5fcfc370d71320326aea1433c17bb42c8aeede1403b1e7e2aff6b80b2b3570b478c06f50c9e4ee6465a599b', 'veterinario', NULL),
('Ana Souza', 'ana', 'scrypt:32768:8:1$gfYVN4lrbtUvYBDd$e4f857259aeb4018f35df3ee77a05ed3877fba72563f70732d220870f8dbdf8dae781e23f0fc680dc9f11c868b21707cd214a38fed5635491183311b7f63058e', 'cliente', 1);

INSERT INTO pets (nome, especie, raca, data_nascimento, cliente_id) VALUES
('Thor', 'Cachorro', 'Golden Retriever', '2020-03-15', 1),
('Mel', 'Gato', 'Siamês', '2021-07-02', 1),
('Bob', 'Cachorro', 'Poodle', '2019-11-20', 2),
('Luna', 'Gato', 'Persa', '2022-01-10', 3),
('Pipoca', 'Roedor', 'Hamster', '2023-05-05', 4),
('Rex', 'Cachorro', 'Pastor Alemão', '2018-09-30', 5);

INSERT INTO servicos (nome, preco, duracao_min) VALUES
('Banho', 50.00, 40),
('Tosa higiênica', 40.00, 30),
('Banho e tosa', 80.00, 90),
('Consulta veterinária', 120.00, 30),
('Vacinação', 90.00, 15);

INSERT INTO agendamentos (pet_id, servico_id, data_hora, status, observacoes) VALUES
(1, 3, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 2 DAY), '09:00:00'), 'Concluído', 'Cliente pediu perfume'),
(3, 1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 1 DAY), '14:00:00'), 'Concluído', NULL),
(4, 5, TIMESTAMP(CURDATE(), '16:30:00'), 'Agendado', 'Vacina V4'),
(2, 4, TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 1 DAY), '10:00:00'), 'Agendado', 'Check-up anual'),
(6, 3, TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 2 DAY), '15:00:00'), 'Agendado', NULL),
(5, 2, TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 3 DAY), '11:00:00'), 'Cancelado', 'Cliente desmarcou');

-- ---------- CONSULTAS PARA A APRESENTAÇÃO (SELECT + JOIN) ----------
-- Pets com o nome do dono
SELECT p.id, p.nome AS pet, p.especie, c.nome AS dono
FROM pets p INNER JOIN clientes c ON c.id = p.cliente_id;

-- Agendamentos completos (4 tabelas)
SELECT a.id, a.data_hora, p.nome AS pet, c.nome AS dono,
       s.nome AS servico, s.preco, a.status
FROM agendamentos a
INNER JOIN pets p ON p.id = a.pet_id
INNER JOIN clientes c ON c.id = p.cliente_id
INNER JOIN servicos s ON s.id = a.servico_id
ORDER BY a.data_hora;

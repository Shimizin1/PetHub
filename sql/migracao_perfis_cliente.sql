-- Conecte no MESMO banco que o admin usa (o DB_NAME da Vercel) e rode antes:
--   USE nome_do_seu_banco;
-- Faça backup antes (ao menos da tabela usuarios).

-- 1) Coluna perfil: se existir como ENUM sem 'cliente', passa a aceitá-lo
SET @tem_perfil := (SELECT COUNT(*) FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'usuarios' AND COLUMN_NAME = 'perfil');
SET @tipo_perfil := (SELECT COLUMN_TYPE FROM information_schema.COLUMNS
                     WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'usuarios' AND COLUMN_NAME = 'perfil');

SET @sql := CASE
  WHEN @tem_perfil = 0 THEN
    "ALTER TABLE usuarios ADD COLUMN perfil VARCHAR(20) NOT NULL DEFAULT 'atendente' AFTER senha_hash"
  WHEN @tipo_perfil LIKE 'enum(%' AND @tipo_perfil NOT LIKE '%cliente%' THEN
    "ALTER TABLE usuarios MODIFY perfil ENUM('administrador','atendente','veterinario','cliente') NOT NULL"
  ELSE "SELECT 'perfil: nada a fazer' AS info"
END;
PREPARE p FROM @sql; EXECUTE p; DEALLOCATE PREPARE p;

-- (só se a coluna perfil acabou de ser criada acima) o admin continua administrador
SET @sql := IF(@tem_perfil = 0,
  "UPDATE usuarios SET perfil = 'administrador' WHERE usuario = 'admin'",
  "SELECT 'perfil: sem ajuste de admin' AS info");
PREPARE p FROM @sql; EXECUTE p; DEALLOCATE PREPARE p;

-- 2) Coluna cliente_id: liga o login do cliente ao cadastro do dono (equipe fica NULL)
SET @tem_cliente_id := (SELECT COUNT(*) FROM information_schema.COLUMNS
                        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'usuarios' AND COLUMN_NAME = 'cliente_id');
SET @sql := IF(@tem_cliente_id = 0,
  "ALTER TABLE usuarios ADD COLUMN cliente_id INT NULL UNIQUE",
  "SELECT 'cliente_id: já existe' AS info");
PREPARE p FROM @sql; EXECUTE p; DEALLOCATE PREPARE p;

-- 3) Chave estrangeira (ao excluir um cliente, o login dele some junto)
SET @tem_fk := (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'usuarios'
                  AND CONSTRAINT_NAME = 'fk_usuarios_clientes');
SET @sql := IF(@tem_fk = 0,
  "ALTER TABLE usuarios ADD CONSTRAINT fk_usuarios_clientes FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE",
  "SELECT 'fk: já existe' AS info");
PREPARE p FROM @sql; EXECUTE p; DEALLOCATE PREPARE p;

-- Conferência
SELECT id, nome, usuario, perfil, cliente_id FROM usuarios;
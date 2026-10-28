-- 0010: Bloqueo temporal de la cuenta tras intentos fallidos de inicio de sesión
-- (requisito: 3 intentos → bloqueo de 15 minutos). locked_until en UTC.

ALTER TABLE `user_account`
  ADD COLUMN `failed_login_attempts` INT NOT NULL DEFAULT 0,
  ADD COLUMN `locked_until` DATETIME(6) NULL;

-- 0014: Política de seguridad configurable por el Administrador de Sistemas (una sola fila).
-- Los CHECK fijan los límites seguros; los valores iniciales (3 intentos, 15 minutos, 8 horas,
-- 8 caracteres) se insertan en 0018.

CREATE TABLE `security_policy` (
  `security_policy_id` BIGINT NOT NULL,
  `max_failed_attempts` INT NOT NULL,
  `lock_minutes` INT NOT NULL,
  `session_hours` INT NOT NULL,
  `min_password_length` INT NOT NULL,
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`security_policy_id`),
  CONSTRAINT `ck_security_policy_single` CHECK (security_policy_id = 1),
  CONSTRAINT `ck_security_policy_attempts` CHECK (max_failed_attempts BETWEEN 3 AND 10),
  CONSTRAINT `ck_security_policy_lock` CHECK (lock_minutes BETWEEN 5 AND 1440),
  CONSTRAINT `ck_security_policy_session` CHECK (session_hours BETWEEN 1 AND 24),
  CONSTRAINT `ck_security_policy_password` CHECK (min_password_length BETWEEN 8 AND 64)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

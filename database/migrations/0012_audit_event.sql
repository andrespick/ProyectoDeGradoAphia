-- 0012: Bitácora de auditoría (inicios de sesión y cambios hechos desde la aplicación).
-- Sin FK hacia user_account: el historial debe sobrevivir a la eliminación de la cuenta, por eso
-- se guarda también el nombre del actor en el momento del evento. Fechas en UTC.
-- No guarda contraseñas, tokens ni el usuario tecleado en intentos contra cuentas inexistentes.

CREATE TABLE `audit_event` (
  `audit_event_id` BIGINT NOT NULL AUTO_INCREMENT,
  `occurred_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `actor_account_id` BIGINT NULL,
  `actor_name` VARCHAR(255) NULL,
  `action` VARCHAR(50) NOT NULL,
  `entity_type` VARCHAR(50) NULL,
  `entity_id` BIGINT NULL,
  `detail` VARCHAR(255) NULL,
  `request_id` CHAR(32) NULL,
  PRIMARY KEY (`audit_event_id`),
  KEY `ix_audit_event_occurred` (`occurred_at`),
  KEY `ix_audit_event_entity` (`entity_type`, `entity_id`),
  KEY `ix_audit_event_actor` (`actor_account_id`, `occurred_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

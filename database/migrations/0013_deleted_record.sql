-- 0013: Papelera. Al eliminar una persona, un inmueble o un contrato se guarda, en la misma
-- transacción, una instantánea JSON con los datos necesarios para volver a registrarlo.
-- El registro original sí se borra (el resto del modelo no cambia); restaurar lo crea de nuevo
-- con otro identificador. Sin FK hacia user_account (ver 0012).

CREATE TABLE `deleted_record` (
  `deleted_record_id` BIGINT NOT NULL AUTO_INCREMENT,
  `entity_type` VARCHAR(50) NOT NULL,
  `entity_id` BIGINT NOT NULL,
  `label` VARCHAR(255) NOT NULL,
  `payload` JSON NOT NULL,
  `deleted_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `deleted_by_account_id` BIGINT NULL,
  `deleted_by_name` VARCHAR(255) NULL,
  PRIMARY KEY (`deleted_record_id`),
  KEY `ix_deleted_record_type` (`entity_type`, `deleted_at`),
  CONSTRAINT `ck_deleted_record_type` CHECK (entity_type IN ('persona', 'inmueble', 'contrato'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

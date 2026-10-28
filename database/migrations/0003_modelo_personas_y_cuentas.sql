-- 0003: Personas, identificación, contacto, cuentas de acceso, roles y cuentas bancarias.
-- Origen: outputs/modelo-bd-3fn/esquema-referencia-mysql.sql (modelo 3FN, 2026-10-21).
-- Sentencias copiadas sin cambios. Fechas en UTC; colación utf8mb4_0900_bin (comparaciones
-- sensibles a mayúsculas y acentos). Decisiones pendientes: docs/arquitectura/modelo-de-datos.md

-- Nombre completo y dirección se conservan; nombre opcional para identidades migradas desde user_account.
CREATE TABLE `person` (
  `person_id` BIGINT NOT NULL AUTO_INCREMENT,
  `person_category_id` BIGINT NULL,
  `full_name` VARCHAR(255) NULL,
  `address` VARCHAR(255) NULL,
  PRIMARY KEY (`person_id`),
  KEY `ix_person_fk1` (`person_category_id`),
  CONSTRAINT `fk_person_1` FOREIGN KEY (`person_category_id`) REFERENCES `person_category` (`person_category_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- Un documento de un tipo y ámbito pertenece a una persona. No fusionar personas sin conciliar conflictos.
CREATE TABLE `person_document` (
  `person_document_id` BIGINT NOT NULL AUTO_INCREMENT,
  `person_id` BIGINT NOT NULL,
  `document_type_id` BIGINT NOT NULL,
  `document_identifier` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`person_document_id`),
  UNIQUE KEY `uq_person_document_1` (`document_type_id`, `document_identifier`),
  KEY `ix_person_document_fk1` (`person_id`),
  CONSTRAINT `fk_person_document_1` FOREIGN KEY (`person_id`) REFERENCES `person` (`person_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `fk_person_document_2` FOREIGN KEY (`document_type_id`) REFERENCES `document_type` (`document_type_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- Mantiene exactamente prefijo y número originales; formato canónico es una validación adicional.
CREATE TABLE `person_phone` (
  `phone_id` BIGINT NOT NULL AUTO_INCREMENT,
  `person_id` BIGINT NOT NULL,
  `phone_prefix` VARCHAR(10) NULL,
  `phone_number` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`phone_id`),
  KEY `ix_person_phone_fk1` (`person_id`),
  CONSTRAINT `fk_person_phone_1` FOREIGN KEY (`person_id`) REFERENCES `person` (`person_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- Correo de contacto; distintas personas pueden compartir una dirección.
CREATE TABLE `person_email` (
  `email_id` BIGINT NOT NULL AUTO_INCREMENT,
  `person_id` BIGINT NOT NULL,
  `email_address` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`email_id`),
  UNIQUE KEY `uq_person_email_1` (`person_id`, `email_address`),
  CONSTRAINT `fk_person_email_1` FOREIGN KEY (`person_id`) REFERENCES `person` (`person_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- Una persona puede tener varias cuentas. Login por user_name; email de acceso separado del contacto.
CREATE TABLE `user_account` (
  `account_id` BIGINT NOT NULL AUTO_INCREMENT,
  `person_id` BIGINT NOT NULL,
  `user_name` VARCHAR(255) NOT NULL,
  `login_email` VARCHAR(255) NULL,
  `hashed_password` VARCHAR(255) NOT NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`account_id`),
  UNIQUE KEY `uq_user_account_1` (`user_name`),
  KEY `ix_user_account_fk1` (`person_id`),
  CONSTRAINT `fk_user_account_1` FOREIGN KEY (`person_id`) REFERENCES `person` (`person_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `ck_user_account_active` CHECK (is_active IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- user_role
CREATE TABLE `user_role` (
  `account_id` BIGINT NOT NULL,
  `role_id` BIGINT NOT NULL,
  PRIMARY KEY (`account_id`, `role_id`),
  CONSTRAINT `fk_user_role_1` FOREIGN KEY (`account_id`) REFERENCES `user_account` (`account_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  KEY `ix_user_role_fk2` (`role_id`),
  CONSTRAINT `fk_user_role_2` FOREIGN KEY (`role_id`) REFERENCES `app_role` (`role_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- account_id es local a esta tabla; no referencia user_account. Un titular por cuenta, como en el original.
CREATE TABLE `bank_account` (
  `account_id` BIGINT NOT NULL AUTO_INCREMENT,
  `person_id` BIGINT NOT NULL,
  `account_identifier` VARCHAR(50) NOT NULL,
  `bank_account_category_id` BIGINT NOT NULL,
  `financial_institution_id` BIGINT NOT NULL,
  PRIMARY KEY (`account_id`),
  KEY `ix_bank_account_fk1` (`person_id`),
  CONSTRAINT `fk_bank_account_1` FOREIGN KEY (`person_id`) REFERENCES `person` (`person_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  KEY `ix_bank_account_fk2` (`bank_account_category_id`),
  CONSTRAINT `fk_bank_account_2` FOREIGN KEY (`bank_account_category_id`) REFERENCES `bank_account_category` (`bank_account_category_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  KEY `ix_bank_account_fk3` (`financial_institution_id`),
  CONSTRAINT `fk_bank_account_3` FOREIGN KEY (`financial_institution_id`) REFERENCES `financial_institution` (`financial_institution_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

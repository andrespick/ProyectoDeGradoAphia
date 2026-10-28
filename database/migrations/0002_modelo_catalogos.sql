-- 0002: Catálogos del modelo 3FN (sin dependencias).
-- Origen: outputs/modelo-bd-3fn/esquema-referencia-mysql.sql (modelo 3FN, 2026-10-21).
-- Sentencias copiadas sin cambios. Fechas en UTC; colación utf8mb4_0900_bin (comparaciones
-- sensibles a mayúsculas y acentos). Decisiones pendientes: docs/arquitectura/modelo-de-datos.md

-- Clasificación original; no determina los roles de un contrato.
CREATE TABLE `person_category` (
  `person_category_id` BIGINT NOT NULL AUTO_INCREMENT,
  `code` VARCHAR(255) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`person_category_id`),
  UNIQUE KEY `uq_person_category_1` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- El ámbito emisor evita asumir que el mismo código documental es universal.
CREATE TABLE `document_type` (
  `document_type_id` BIGINT NOT NULL AUTO_INCREMENT,
  `issuer_scope` VARCHAR(100) NOT NULL,
  `code` VARCHAR(255) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`document_type_id`),
  UNIQUE KEY `uq_document_type_1` (`issuer_scope`, `code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- Conserva userCategory; no presupone permisos a partir del nombre.
CREATE TABLE `app_role` (
  `role_id` BIGINT NOT NULL AUTO_INCREMENT,
  `code` VARCHAR(255) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`role_id`),
  UNIQUE KEY `uq_app_role_1` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- Nombre original conservado; no es globalmente único. Región y país requieren enriquecimiento verificado.
CREATE TABLE `city` (
  `city_id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `region_name` VARCHAR(255) NULL,
  `country_code` CHAR(2) NULL,
  PRIMARY KEY (`city_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- Estado operativo original; no se infiere automáticamente de los contratos.
CREATE TABLE `occupancy_state` (
  `occupancy_state_id` BIGINT NOT NULL AUTO_INCREMENT,
  `code` VARCHAR(255) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`occupancy_state_id`),
  UNIQUE KEY `uq_occupancy_state_1` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- Moneda explícita; no asignar COP u otra moneda a datos antiguos sin confirmación.
CREATE TABLE `currency` (
  `currency_code` CHAR(3) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`currency_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- Tipo de servicio; nullable en contratos migrados sin desagregación confirmada.
CREATE TABLE `utility_type` (
  `utility_type_id` BIGINT NOT NULL AUTO_INCREMENT,
  `code` VARCHAR(255) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`utility_type_id`),
  UNIQUE KEY `uq_utility_type_1` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- service_provider
CREATE TABLE `service_provider` (
  `provider_id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`provider_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- agreement_category
CREATE TABLE `agreement_category` (
  `agreement_category_id` BIGINT NOT NULL AUTO_INCREMENT,
  `code` VARCHAR(255) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`agreement_category_id`),
  UNIQUE KEY `uq_agreement_category_1` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- ASSOCIATED y CO_DEBTOR preservan los dos vínculos originales.
CREATE TABLE `party_role` (
  `party_role_id` BIGINT NOT NULL AUTO_INCREMENT,
  `code` VARCHAR(255) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`party_role_id`),
  UNIQUE KEY `uq_party_role_1` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- Mantiene recordCategory; dirección y naturaleza deben definirse por negocio.
CREATE TABLE `financial_category` (
  `financial_category_id` BIGINT NOT NULL AUTO_INCREMENT,
  `code` VARCHAR(255) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`financial_category_id`),
  UNIQUE KEY `uq_financial_category_1` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- Estado original del registro; no se calcula un saldo sin definir cargos y pagos.
CREATE TABLE `payment_state` (
  `payment_state_id` BIGINT NOT NULL AUTO_INCREMENT,
  `code` VARCHAR(255) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`payment_state_id`),
  UNIQUE KEY `uq_payment_state_1` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- bank_account_category
CREATE TABLE `bank_account_category` (
  `bank_account_category_id` BIGINT NOT NULL AUTO_INCREMENT,
  `code` VARCHAR(255) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`bank_account_category_id`),
  UNIQUE KEY `uq_bank_account_category_1` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- financial_institution
CREATE TABLE `financial_institution` (
  `financial_institution_id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`financial_institution_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- file_category
CREATE TABLE `file_category` (
  `file_category_id` BIGINT NOT NULL AUTO_INCREMENT,
  `code` VARCHAR(255) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`file_category_id`),
  UNIQUE KEY `uq_file_category_1` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

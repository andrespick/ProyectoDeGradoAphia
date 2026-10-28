-- 0005: Acuerdos (contratos) de inmuebles, participantes y registros financieros.
-- Origen: outputs/modelo-bd-3fn/esquema-referencia-mysql.sql (modelo 3FN, 2026-10-21).
-- Sentencias copiadas sin cambios. Fechas en UTC; colación utf8mb4_0900_bin (comparaciones
-- sensibles a mayúsculas y acentos). Decisiones pendientes: docs/arquitectura/modelo-de-datos.md

-- Un acuerdo por inmueble, como en el original. Canon pactado nuevo: no reconstruirlo copiando el canon actual.
CREATE TABLE `property_agreement` (
  `agreement_id` BIGINT NOT NULL AUTO_INCREMENT,
  `agreement_category_id` BIGINT NOT NULL,
  `property_id` BIGINT NOT NULL,
  `start_date` DATE NOT NULL,
  `end_date` DATE NULL,
  `agreement_content` LONGTEXT NULL,
  `conditions` TEXT NULL,
  `agreed_rental_value` DECIMAL(12,2) NULL,
  `currency_code` CHAR(3) NULL,
  PRIMARY KEY (`agreement_id`),
  KEY `ix_property_agreement_fk1` (`agreement_category_id`),
  CONSTRAINT `fk_property_agreement_1` FOREIGN KEY (`agreement_category_id`) REFERENCES `agreement_category` (`agreement_category_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  KEY `ix_property_agreement_fk2` (`property_id`),
  CONSTRAINT `fk_property_agreement_2` FOREIGN KEY (`property_id`) REFERENCES `property` (`property_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  KEY `ix_property_agreement_fk3` (`currency_code`),
  CONSTRAINT `fk_property_agreement_3` FOREIGN KEY (`currency_code`) REFERENCES `currency` (`currency_code`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `ck_property_agreement_valid_dates` CHECK (end_date IS NULL OR end_date >= start_date),
  CONSTRAINT `ck_property_agreement_agreed_nonnegative` CHECK (agreed_rental_value IS NULL OR agreed_rental_value >= 0),
  CONSTRAINT `ck_property_agreement_agreed_currency` CHECK (agreed_rental_value IS NULL OR currency_code IS NOT NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- La PK completa permite varios codeudores sin duplicar una persona con el mismo rol en un acuerdo.
CREATE TABLE `agreement_party` (
  `agreement_id` BIGINT NOT NULL,
  `person_id` BIGINT NOT NULL,
  `party_role_id` BIGINT NOT NULL,
  PRIMARY KEY (`agreement_id`, `person_id`, `party_role_id`),
  CONSTRAINT `fk_agreement_party_1` FOREIGN KEY (`agreement_id`) REFERENCES `property_agreement` (`agreement_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  KEY `ix_agreement_party_fk2` (`person_id`),
  CONSTRAINT `fk_agreement_party_2` FOREIGN KEY (`person_id`) REFERENCES `person` (`person_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  KEY `ix_agreement_party_fk3` (`party_role_id`),
  CONSTRAINT `fk_agreement_party_3` FOREIGN KEY (`party_role_id`) REFERENCES `party_role` (`party_role_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- Se conserva la semántica original; no se impone amount > 0 sin saber cómo se registran reversos o abonos.
CREATE TABLE `financial_record` (
  `record_id` BIGINT NOT NULL AUTO_INCREMENT,
  `agreement_id` BIGINT NOT NULL,
  `financial_category_id` BIGINT NOT NULL,
  `amount` DECIMAL(12,2) NOT NULL,
  `record_date` DATE NOT NULL,
  `payment_state_id` BIGINT NOT NULL,
  `currency_code` CHAR(3) NOT NULL,
  PRIMARY KEY (`record_id`),
  KEY `ix_financial_record_fk1` (`agreement_id`),
  CONSTRAINT `fk_financial_record_1` FOREIGN KEY (`agreement_id`) REFERENCES `property_agreement` (`agreement_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  KEY `ix_financial_record_fk2` (`financial_category_id`),
  CONSTRAINT `fk_financial_record_2` FOREIGN KEY (`financial_category_id`) REFERENCES `financial_category` (`financial_category_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  KEY `ix_financial_record_fk3` (`payment_state_id`),
  CONSTRAINT `fk_financial_record_3` FOREIGN KEY (`payment_state_id`) REFERENCES `payment_state` (`payment_state_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  KEY `ix_financial_record_fk4` (`currency_code`),
  CONSTRAINT `fk_financial_record_4` FOREIGN KEY (`currency_code`) REFERENCES `currency` (`currency_code`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

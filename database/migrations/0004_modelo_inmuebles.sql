-- 0004: Inmuebles, propietarios y contratos de servicios públicos.
-- Origen: outputs/modelo-bd-3fn/esquema-referencia-mysql.sql (modelo 3FN, 2026-10-21).
-- Sentencias copiadas sin cambios. Fechas en UTC; colación utf8mb4_0900_bin (comparaciones
-- sensibles a mayúsculas y acentos). Decisiones pendientes: docs/arquitectura/modelo-de-datos.md

-- Canon de oferta/referencia del inmueble; no sustituye el canon pactado de un contrato histórico.
CREATE TABLE `property` (
  `property_id` BIGINT NOT NULL AUTO_INCREMENT,
  `address` VARCHAR(255) NOT NULL,
  `city_id` BIGINT NULL,
  `registration_identifier` VARCHAR(255) NULL,
  `rental_value` DECIMAL(12,2) NULL,
  `currency_code` CHAR(3) NULL,
  `occupancy_state_id` BIGINT NULL,
  PRIMARY KEY (`property_id`),
  KEY `ix_property_fk1` (`city_id`),
  CONSTRAINT `fk_property_1` FOREIGN KEY (`city_id`) REFERENCES `city` (`city_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  KEY `ix_property_fk2` (`currency_code`),
  CONSTRAINT `fk_property_2` FOREIGN KEY (`currency_code`) REFERENCES `currency` (`currency_code`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  KEY `ix_property_fk3` (`occupancy_state_id`),
  CONSTRAINT `fk_property_3` FOREIGN KEY (`occupancy_state_id`) REFERENCES `occupancy_state` (`occupancy_state_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `ck_property_rental_nonnegative` CHECK (rental_value IS NULL OR rental_value >= 0),
  CONSTRAINT `ck_property_rental_currency` CHECK (rental_value IS NULL OR currency_code IS NOT NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- Cada ownerId original genera una fila; admite copropiedad.
CREATE TABLE `property_owner` (
  `property_id` BIGINT NOT NULL,
  `person_id` BIGINT NOT NULL,
  PRIMARY KEY (`property_id`, `person_id`),
  CONSTRAINT `fk_property_owner_1` FOREIGN KEY (`property_id`) REFERENCES `property` (`property_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  KEY `ix_property_owner_fk2` (`person_id`),
  CONSTRAINT `fk_property_owner_2` FOREIGN KEY (`person_id`) REFERENCES `person` (`person_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- Una fila por contrato de servicio verificado. El texto compuesto original queda en el archivo de migración.
CREATE TABLE `property_utility` (
  `property_utility_id` BIGINT NOT NULL AUTO_INCREMENT,
  `property_id` BIGINT NOT NULL,
  `utility_type_id` BIGINT NULL,
  `provider_id` BIGINT NULL,
  `contract_identifier` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`property_utility_id`),
  KEY `ix_property_utility_fk1` (`property_id`),
  CONSTRAINT `fk_property_utility_1` FOREIGN KEY (`property_id`) REFERENCES `property` (`property_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  KEY `ix_property_utility_fk2` (`utility_type_id`),
  CONSTRAINT `fk_property_utility_2` FOREIGN KEY (`utility_type_id`) REFERENCES `utility_type` (`utility_type_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  KEY `ix_property_utility_fk3` (`provider_id`),
  CONSTRAINT `fk_property_utility_3` FOREIGN KEY (`provider_id`) REFERENCES `service_provider` (`provider_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

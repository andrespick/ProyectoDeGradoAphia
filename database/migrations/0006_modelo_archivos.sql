-- 0006: Metadatos de archivos y sus vínculos con personas, inmuebles y acuerdos.
-- Origen: outputs/modelo-bd-3fn/esquema-referencia-mysql.sql (modelo 3FN, 2026-10-21).
-- Sentencias copiadas sin cambios. Fechas en UTC; colación utf8mb4_0900_bin (comparaciones
-- sensibles a mayúsculas y acentos). Decisiones pendientes: docs/arquitectura/modelo-de-datos.md

-- upload_date conserva la fecha original sin inventar una hora. Hash nullable y no único; no elimina archivos repetidos.
CREATE TABLE `file_record` (
  `file_id` BIGINT NOT NULL AUTO_INCREMENT,
  `file_name` VARCHAR(255) NOT NULL,
  `file_category_id` BIGINT NOT NULL,
  `file_path` TEXT NOT NULL,
  `upload_date` DATE NOT NULL,
  `sha256` BINARY(32) NULL,
  `size_bytes` BIGINT NULL,
  `mime_type` VARCHAR(127) NULL,
  PRIMARY KEY (`file_id`),
  KEY `ix_file_record_fk1` (`file_category_id`),
  CONSTRAINT `fk_file_record_1` FOREIGN KEY (`file_category_id`) REFERENCES `file_category` (`file_category_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `ck_file_record_file_size` CHECK (size_bytes IS NULL OR size_bytes >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- file_person
CREATE TABLE `file_person` (
  `file_id` BIGINT NOT NULL,
  `person_id` BIGINT NOT NULL,
  PRIMARY KEY (`file_id`, `person_id`),
  CONSTRAINT `fk_file_person_1` FOREIGN KEY (`file_id`) REFERENCES `file_record` (`file_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  KEY `ix_file_person_fk2` (`person_id`),
  CONSTRAINT `fk_file_person_2` FOREIGN KEY (`person_id`) REFERENCES `person` (`person_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- file_property
CREATE TABLE `file_property` (
  `file_id` BIGINT NOT NULL,
  `property_id` BIGINT NOT NULL,
  PRIMARY KEY (`file_id`, `property_id`),
  CONSTRAINT `fk_file_property_1` FOREIGN KEY (`file_id`) REFERENCES `file_record` (`file_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  KEY `ix_file_property_fk2` (`property_id`),
  CONSTRAINT `fk_file_property_2` FOREIGN KEY (`property_id`) REFERENCES `property` (`property_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

-- Extensión nueva para anexos de acuerdos.
CREATE TABLE `file_agreement` (
  `file_id` BIGINT NOT NULL,
  `agreement_id` BIGINT NOT NULL,
  PRIMARY KEY (`file_id`, `agreement_id`),
  CONSTRAINT `fk_file_agreement_1` FOREIGN KEY (`file_id`) REFERENCES `file_record` (`file_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  KEY `ix_file_agreement_fk2` (`agreement_id`),
  CONSTRAINT `fk_file_agreement_2` FOREIGN KEY (`agreement_id`) REFERENCES `property_agreement` (`agreement_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

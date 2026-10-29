-- 0015: Datos de la empresa (una sola fila) para la impresión de contratos y el pie de página.
-- El logotipo no es configurable: sigue siendo el archivo estático de la web.

CREATE TABLE `organization_profile` (
  `organization_profile_id` BIGINT NOT NULL,
  `legal_name` VARCHAR(255) NOT NULL,
  `tax_identifier` VARCHAR(50) NULL,
  `address` VARCHAR(255) NULL,
  `city_id` BIGINT NULL,
  `phone_number` VARCHAR(50) NULL,
  `email_address` VARCHAR(255) NULL,
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`organization_profile_id`),
  KEY `ix_organization_profile_fk1` (`city_id`),
  CONSTRAINT `fk_organization_profile_1` FOREIGN KEY (`city_id`) REFERENCES `city` (`city_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `ck_organization_profile_single` CHECK (organization_profile_id = 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

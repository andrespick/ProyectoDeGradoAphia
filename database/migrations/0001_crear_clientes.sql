-- 0001: tabla mínima de clientes para validar la arquitectura.
-- No representa todavía el modelo de datos empresarial de APHIA.

CREATE TABLE clientes (
    id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    nombre         VARCHAR(150)    NOT NULL,
    correo         VARCHAR(254)    NOT NULL,
    creado_en      DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    actualizado_en DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_clientes_correo (correo)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

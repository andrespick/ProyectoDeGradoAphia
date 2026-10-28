-- 0007: Índices de consulta iniciales; confirmar con EXPLAIN y carga real.
-- Origen: outputs/modelo-bd-3fn/esquema-referencia-mysql.sql (modelo 3FN, 2026-10-21).
-- Sentencias copiadas sin cambios. Fechas en UTC; colación utf8mb4_0900_bin (comparaciones
-- sensibles a mayúsculas y acentos). Decisiones pendientes: docs/arquitectura/modelo-de-datos.md

-- Índices de consulta iniciales; confirmar con EXPLAIN y carga real.
CREATE INDEX `ix_financial_agreement_date` ON `financial_record` (`agreement_id`, `record_date`);
CREATE INDEX `ix_agreement_property_dates` ON `property_agreement` (`property_id`, `start_date`, `end_date`);
CREATE INDEX `ix_agreement_party_person` ON `agreement_party` (`person_id`, `agreement_id`);

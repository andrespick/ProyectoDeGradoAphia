-- 0019: Nombre único de banco. La aplicación busca o crea el banco por nombre exacto; sin la
-- restricción, dos registros simultáneos con el mismo banco nuevo dejaban dos filas iguales.
-- Antes de aplicarla compruebe que no hay duplicados (la migración fallaría):
--   SELECT name, COUNT(*) FROM financial_institution GROUP BY name HAVING COUNT(*) > 1;

ALTER TABLE `financial_institution`
  ADD UNIQUE KEY `uq_financial_institution_name` (`name`);

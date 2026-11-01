-- 0020: Nombre único de proveedor de servicios, por el mismo motivo que 0019.
-- Las ciudades no se tocan: su unicidad es una decisión pendiente del modelo de datos.
-- Antes de aplicarla compruebe que no hay duplicados (la migración fallaría):
--   SELECT name, COUNT(*) FROM service_provider GROUP BY name HAVING COUNT(*) > 1;

ALTER TABLE `service_provider`
  ADD UNIQUE KEY `uq_service_provider_name` (`name`);

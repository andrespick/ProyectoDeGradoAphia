-- 0008: Valores de referencia que la API usa por código. Deben existir en todos los entornos
-- (producción incluida); por eso van en una migración y no en database/seeds.
-- Los nombres de ciudades, bancos y proveedores NO van aquí: la aplicación los crea por nombre.
-- Decisiones: docs/arquitectura/modelo-de-datos.md («Migraciones 0008–0010»).

INSERT INTO `app_role` (`code`, `name`) VALUES
  ('ADMIN_SISTEMAS', 'Administrador de Sistemas'),
  ('ADMINISTRATIVO', 'Administrativo'),
  ('ASESOR', 'Asesor');

-- Papeles de una persona frente a la inmobiliaria y en un contrato. No se crea ASSOCIATED:
-- el «cliente asociado» del modelo original equivale a TENANT (arrendatario).
INSERT INTO `party_role` (`code`, `name`) VALUES
  ('OWNER', 'Propietario'),
  ('TENANT', 'Arrendatario'),
  ('CO_DEBTOR', 'Codeudor');

INSERT INTO `occupancy_state` (`code`, `name`) VALUES
  ('DISPONIBLE', 'Disponible'),
  ('OCUPADO', 'Ocupado');

INSERT INTO `currency` (`currency_code`, `name`) VALUES ('COP', 'Peso colombiano');

INSERT INTO `document_type` (`issuer_scope`, `code`, `name`) VALUES
  ('CO', 'CC', 'Cédula de ciudadanía'),
  ('CO', 'CE', 'Cédula de extranjería'),
  ('CO', 'NIT', 'NIT'),
  ('CO', 'PAS', 'Pasaporte'),
  ('CO', 'TI', 'Tarjeta de identidad');

INSERT INTO `agreement_category` (`code`, `name`) VALUES
  ('ARRENDAMIENTO', 'Arrendamiento'),
  ('ADMINISTRACION', 'Administración');

INSERT INTO `bank_account_category` (`code`, `name`) VALUES
  ('AHORROS', 'Ahorros'),
  ('CORRIENTE', 'Corriente');

INSERT INTO `utility_type` (`code`, `name`) VALUES
  ('AGUA', 'Acueducto y alcantarillado'),
  ('ENERGIA', 'Energía'),
  ('GAS', 'Gas'),
  ('INTERNET', 'Internet y telefonía'),
  ('ASEO', 'Aseo');

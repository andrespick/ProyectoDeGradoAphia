-- Catálogos de nombre libre para desarrollo (ciudades, bancos, proveedores de servicios).
-- Idempotente: ids altos fijos (9001…) que no chocan con los que crea la aplicación.
-- Los códigos de los que depende la API están en la migración 0008.

INSERT INTO city (city_id, name, region_name, country_code) VALUES
    (9001, 'Bogotá', 'Cundinamarca', 'CO'),
    (9002, 'Medellín', 'Antioquia', 'CO'),
    (9003, 'Cali', 'Valle del Cauca', 'CO'),
    (9004, 'Barranquilla', 'Atlántico', 'CO'),
    (9005, 'Bucaramanga', 'Santander', 'CO')
AS nuevos
ON DUPLICATE KEY UPDATE name = nuevos.name, region_name = nuevos.region_name;

INSERT INTO financial_institution (financial_institution_id, name) VALUES
    (9001, 'Bancolombia'),
    (9002, 'Davivienda'),
    (9003, 'Banco de Bogotá'),
    (9004, 'BBVA Colombia'),
    (9005, 'Nequi')
AS nuevos
ON DUPLICATE KEY UPDATE name = nuevos.name;

INSERT INTO service_provider (provider_id, name) VALUES
    (9001, 'EPM'),
    (9002, 'Enel Colombia'),
    (9003, 'Acueducto de Bogotá'),
    (9004, 'Vanti'),
    (9005, 'Claro')
AS nuevos
ON DUPLICATE KEY UPDATE name = nuevos.name;

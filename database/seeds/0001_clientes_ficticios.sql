-- Datos ficticios para desarrollo y pruebas. Dominio reservado .test (RFC 2606).
-- Idempotente: puede ejecutarse varias veces.

INSERT INTO clientes (nombre, correo) VALUES
    ('Cliente Ficticio Uno', 'cliente.uno@example.test'),
    ('Cliente Ficticio Dos', 'cliente.dos@example.test'),
    ('Cliente Ficticio Tres', 'cliente.tres@example.test')
AS nuevos
ON DUPLICATE KEY UPDATE nombre = nuevos.nombre;

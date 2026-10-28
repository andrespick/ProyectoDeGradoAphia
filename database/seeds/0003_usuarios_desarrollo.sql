-- Usuarios de desarrollo: admin / administrativo / asesor, todos con la contraseña «Aphia.2026».
-- SOLO para development y test (seed.py se niega a ejecutarse en otros entornos).
-- Hash: PBKDF2-SHA256, 100000 iteraciones (apps/api/src/modules/auth/passwords.py).
-- Idempotente: volver a cargarlo restablece la contraseña, reactiva y desbloquea las cuentas.

INSERT INTO person (person_id, full_name) VALUES
    (9001, 'Administradora de Sistemas (ficticia)'),
    (9002, 'Persona Administrativa (ficticia)'),
    (9003, 'Asesor Ficticio')
AS nuevos
ON DUPLICATE KEY UPDATE full_name = nuevos.full_name;

INSERT INTO person_document (person_document_id, person_id, document_type_id, document_identifier)
SELECT 9001, 9001, document_type_id, '900000001' FROM document_type WHERE issuer_scope = 'CO' AND code = 'CC'
ON DUPLICATE KEY UPDATE document_identifier = '900000001';

INSERT INTO person_document (person_document_id, person_id, document_type_id, document_identifier)
SELECT 9002, 9002, document_type_id, '900000002' FROM document_type WHERE issuer_scope = 'CO' AND code = 'CC'
ON DUPLICATE KEY UPDATE document_identifier = '900000002';

INSERT INTO person_document (person_document_id, person_id, document_type_id, document_identifier)
SELECT 9003, 9003, document_type_id, '900000003' FROM document_type WHERE issuer_scope = 'CO' AND code = 'CC'
ON DUPLICATE KEY UPDATE document_identifier = '900000003';

INSERT INTO user_account (account_id, person_id, user_name, login_email, hashed_password) VALUES
    (9001, 9001, 'admin', 'admin@example.test', 'pbkdf2_sha256$100000$BMEA7iSnVcXVgxLVaPvShA==$YavUqH5jCXl4qzQrpOEuU/gkoecM/tVRoOdKfvTWRfQ='),
    (9002, 9002, 'administrativo', 'administrativo@example.test', 'pbkdf2_sha256$100000$BMEA7iSnVcXVgxLVaPvShA==$YavUqH5jCXl4qzQrpOEuU/gkoecM/tVRoOdKfvTWRfQ='),
    (9003, 9003, 'asesor', 'asesor@example.test', 'pbkdf2_sha256$100000$BMEA7iSnVcXVgxLVaPvShA==$YavUqH5jCXl4qzQrpOEuU/gkoecM/tVRoOdKfvTWRfQ=')
AS nuevos
ON DUPLICATE KEY UPDATE hashed_password = nuevos.hashed_password, is_active = 1,
    failed_login_attempts = 0, locked_until = NULL;

INSERT IGNORE INTO user_role (account_id, role_id)
SELECT 9001, role_id FROM app_role WHERE code = 'ADMIN_SISTEMAS';

INSERT IGNORE INTO user_role (account_id, role_id)
SELECT 9002, role_id FROM app_role WHERE code = 'ADMINISTRATIVO';

INSERT IGNORE INTO user_role (account_id, role_id)
SELECT 9003, role_id FROM app_role WHERE code = 'ASESOR';

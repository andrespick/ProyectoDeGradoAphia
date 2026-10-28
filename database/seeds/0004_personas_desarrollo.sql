-- Personas ficticias para desarrollo: propietarios, arrendatarios y codeudores (una persona
-- puede tener varios papeles: 9103 es propietario y codeudor). Dominio reservado .test.
-- Idempotente: ids fijos (9101…) que no chocan con los que crea la aplicación.

INSERT INTO person (person_id, full_name, address) VALUES
    (9101, 'Laura Propietaria Ficticia', 'Calle 10 # 5-20, Bogotá'),
    (9102, 'Carlos Arrendatario Ficticio', 'Carrera 7 # 45-10, Bogotá'),
    (9103, 'Mario Propietario y Codeudor Ficticio', 'Calle 50 # 20-30, Medellín'),
    (9104, 'Ana Arrendataria Ficticia', NULL),
    (9105, 'Pedro Codeudor Ficticio', NULL),
    (9106, 'Sofía Codeudora Ficticia', 'Avenida 3 # 12-40, Cali')
AS nuevos
ON DUPLICATE KEY UPDATE full_name = nuevos.full_name, address = nuevos.address;

INSERT INTO person_document (person_document_id, person_id, document_type_id, document_identifier)
SELECT 9101, 9101, document_type_id, '1000009101' FROM document_type WHERE issuer_scope = 'CO' AND code = 'CC'
ON DUPLICATE KEY UPDATE document_identifier = '1000009101';
INSERT INTO person_document (person_document_id, person_id, document_type_id, document_identifier)
SELECT 9102, 9102, document_type_id, '1000009102' FROM document_type WHERE issuer_scope = 'CO' AND code = 'CC'
ON DUPLICATE KEY UPDATE document_identifier = '1000009102';
INSERT INTO person_document (person_document_id, person_id, document_type_id, document_identifier)
SELECT 9103, 9103, document_type_id, '1000009103' FROM document_type WHERE issuer_scope = 'CO' AND code = 'CC'
ON DUPLICATE KEY UPDATE document_identifier = '1000009103';
INSERT INTO person_document (person_document_id, person_id, document_type_id, document_identifier)
SELECT 9104, 9104, document_type_id, '1000009104' FROM document_type WHERE issuer_scope = 'CO' AND code = 'CC'
ON DUPLICATE KEY UPDATE document_identifier = '1000009104';
INSERT INTO person_document (person_document_id, person_id, document_type_id, document_identifier)
SELECT 9105, 9105, document_type_id, '1000009105' FROM document_type WHERE issuer_scope = 'CO' AND code = 'CE'
ON DUPLICATE KEY UPDATE document_identifier = '1000009105';
INSERT INTO person_document (person_document_id, person_id, document_type_id, document_identifier)
SELECT 9106, 9106, document_type_id, '1000009106' FROM document_type WHERE issuer_scope = 'CO' AND code = 'CC'
ON DUPLICATE KEY UPDATE document_identifier = '1000009106';

INSERT INTO person_phone (phone_id, person_id, phone_prefix, phone_number) VALUES
    (9101, 9101, '+57', '3000009101'),
    (9102, 9102, '+57', '3000009102'),
    (9103, 9103, '+57', '3000009103'),
    (9104, 9104, '+57', '3000009104'),
    (9105, 9105, '+57', '3000009105'),
    (9106, 9106, '+57', '3000009106')
AS nuevos
ON DUPLICATE KEY UPDATE phone_number = nuevos.phone_number;

INSERT INTO person_email (email_id, person_id, email_address) VALUES
    (9101, 9101, 'persona9101@example.test'),
    (9102, 9102, 'persona9102@example.test'),
    (9103, 9103, 'persona9103@example.test'),
    (9104, 9104, 'persona9104@example.test'),
    (9105, 9105, 'persona9105@example.test'),
    (9106, 9106, 'persona9106@example.test')
AS nuevos
ON DUPLICATE KEY UPDATE email_address = nuevos.email_address;

INSERT IGNORE INTO person_party_role (person_id, party_role_id)
SELECT 9101, party_role_id FROM party_role WHERE code = 'OWNER';
INSERT IGNORE INTO person_party_role (person_id, party_role_id)
SELECT 9102, party_role_id FROM party_role WHERE code = 'TENANT';
INSERT IGNORE INTO person_party_role (person_id, party_role_id)
SELECT 9103, party_role_id FROM party_role WHERE code = 'OWNER';
INSERT IGNORE INTO person_party_role (person_id, party_role_id)
SELECT 9103, party_role_id FROM party_role WHERE code = 'CO_DEBTOR';
INSERT IGNORE INTO person_party_role (person_id, party_role_id)
SELECT 9104, party_role_id FROM party_role WHERE code = 'TENANT';
INSERT IGNORE INTO person_party_role (person_id, party_role_id)
SELECT 9105, party_role_id FROM party_role WHERE code = 'CO_DEBTOR';
INSERT IGNORE INTO person_party_role (person_id, party_role_id)
SELECT 9106, party_role_id FROM party_role WHERE code = 'CO_DEBTOR';

INSERT INTO bank_account (account_id, person_id, account_identifier, bank_account_category_id, financial_institution_id)
SELECT 9101, 9101, '0123456789', bank_account_category_id, 9001 FROM bank_account_category WHERE code = 'AHORROS'
ON DUPLICATE KEY UPDATE account_identifier = '0123456789';
INSERT INTO bank_account (account_id, person_id, account_identifier, bank_account_category_id, financial_institution_id)
SELECT 9103, 9103, '9876543210', bank_account_category_id, 9002 FROM bank_account_category WHERE code = 'CORRIENTE'
ON DUPLICATE KEY UPDATE account_identifier = '9876543210';

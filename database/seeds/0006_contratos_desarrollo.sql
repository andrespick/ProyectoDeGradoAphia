-- Contratos ficticios de desarrollo sobre los inmuebles 9202 y 9203 (seed 0005) y las
-- personas 9101–9106 (seed 0004). Idempotente: ids fijos (9301…). Textos de una sola línea.
INSERT INTO property_agreement (agreement_id, agreement_category_id, property_id, start_date, end_date, agreement_content, conditions, agreed_rental_value, currency_code)
SELECT 9301, agreement_category_id, 9202, '2026-01-01', '2026-12-31', 'CONTRATO DE ARRENDAMIENTO DE LOCAL COMERCIAL (texto ficticio de desarrollo). Entre los suscritos, LAURA PROPIETARIA FICTICIA y MARIO PROPIETARIO Y CODEUDOR FICTICIO, en calidad de arrendadores, y CARLOS ARRENDATARIO FICTICIO, en calidad de arrendatario, se celebra el presente contrato sobre el inmueble ubicado en Carrera 43A # 7 Sur-170, Local 104, Medellín, por un canon mensual de $1.500.000 COP, con vigencia del 1 de enero al 31 de diciembre de 2026. Codeudores solidarios: PEDRO CODEUDOR FICTICIO y SOFÍA CODEUDORA FICTICIA.', 'Pago dentro de los cinco primeros días de cada mes. Incremento anual según IPC. Prohibido el subarriendo.', 1500000.00, 'COP'
FROM agreement_category WHERE code = 'ARRENDAMIENTO'
ON DUPLICATE KEY UPDATE start_date = VALUES(start_date), end_date = VALUES(end_date), agreed_rental_value = VALUES(agreed_rental_value), currency_code = VALUES(currency_code);
INSERT INTO property_agreement (agreement_id, agreement_category_id, property_id, start_date, end_date, agreement_content, conditions, agreed_rental_value, currency_code)
SELECT 9302, agreement_category_id, 9203, '2026-03-01', NULL, NULL, 'Administración integral de la oficina 801: recaudo, mantenimiento y atención de arrendatarios (datos ficticios).', NULL, NULL
FROM agreement_category WHERE code = 'ADMINISTRACION'
ON DUPLICATE KEY UPDATE start_date = VALUES(start_date), end_date = VALUES(end_date);
INSERT IGNORE INTO agreement_party (agreement_id, person_id, party_role_id)
SELECT 9301, 9101, party_role_id FROM party_role WHERE code = 'OWNER';
INSERT IGNORE INTO agreement_party (agreement_id, person_id, party_role_id)
SELECT 9301, 9103, party_role_id FROM party_role WHERE code = 'OWNER';
INSERT IGNORE INTO agreement_party (agreement_id, person_id, party_role_id)
SELECT 9301, 9102, party_role_id FROM party_role WHERE code = 'TENANT';
INSERT IGNORE INTO agreement_party (agreement_id, person_id, party_role_id)
SELECT 9301, 9105, party_role_id FROM party_role WHERE code = 'CO_DEBTOR';
INSERT IGNORE INTO agreement_party (agreement_id, person_id, party_role_id)
SELECT 9301, 9106, party_role_id FROM party_role WHERE code = 'CO_DEBTOR';
INSERT IGNORE INTO agreement_party (agreement_id, person_id, party_role_id)
SELECT 9302, 9103, party_role_id FROM party_role WHERE code = 'OWNER';
INSERT IGNORE INTO agreement_party (agreement_id, person_id, party_role_id)
SELECT 9302, 9104, party_role_id FROM party_role WHERE code = 'TENANT';
INSERT IGNORE INTO agreement_party (agreement_id, person_id, party_role_id)
SELECT 9302, 9105, party_role_id FROM party_role WHERE code = 'CO_DEBTOR';
INSERT IGNORE INTO person_party_role (person_id, party_role_id)
SELECT 9106, party_role_id FROM party_role WHERE code = 'CO_DEBTOR';

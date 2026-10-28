-- Inmuebles ficticios para desarrollo (ciudades del seed 0002, propietarios del seed 0004).
-- Idempotente: ids fijos (9201…).

INSERT INTO property (property_id, address, city_id, registration_identifier, rental_value, currency_code, occupancy_state_id)
SELECT 9201, 'Calle 93B # 11A-44, Apto 502', 9001, '50C-184920', 1500000.00, 'COP', occupancy_state_id
FROM occupancy_state WHERE code = 'DISPONIBLE'
ON DUPLICATE KEY UPDATE address = 'Calle 93B # 11A-44, Apto 502';
INSERT INTO property (property_id, address, city_id, registration_identifier, rental_value, currency_code, occupancy_state_id)
SELECT 9202, 'Carrera 43A # 7 Sur-170, Local 104', 9002, '01N-449102', 2200000.00, 'COP', occupancy_state_id
FROM occupancy_state WHERE code = 'OCUPADO'
ON DUPLICATE KEY UPDATE address = 'Carrera 43A # 7 Sur-170, Local 104';
INSERT INTO property (property_id, address, city_id, registration_identifier, rental_value, currency_code, occupancy_state_id)
SELECT 9203, 'Calle 100 # 8A-55, Oficina 801', 9001, '50N-290194', NULL, NULL, occupancy_state_id
FROM occupancy_state WHERE code = 'DISPONIBLE'
ON DUPLICATE KEY UPDATE address = 'Calle 100 # 8A-55, Oficina 801';

INSERT IGNORE INTO property_owner (property_id, person_id) VALUES
    (9201, 9101),
    (9202, 9101),
    (9202, 9103),
    (9203, 9103);

INSERT INTO property_utility (property_utility_id, property_id, utility_type_id, provider_id, contract_identifier)
SELECT 9201, 9201, utility_type_id, 9002, 'ENEL-740192' FROM utility_type WHERE code = 'ENERGIA'
ON DUPLICATE KEY UPDATE contract_identifier = 'ENEL-740192';
INSERT INTO property_utility (property_utility_id, property_id, utility_type_id, provider_id, contract_identifier)
SELECT 9202, 9201, utility_type_id, 9003, 'ACU-882019' FROM utility_type WHERE code = 'AGUA'
ON DUPLICATE KEY UPDATE contract_identifier = 'ACU-882019';
INSERT INTO property_utility (property_utility_id, property_id, utility_type_id, provider_id, contract_identifier)
SELECT 9203, 9202, utility_type_id, 9001, 'EPM-209481' FROM utility_type WHERE code = 'ENERGIA'
ON DUPLICATE KEY UPDATE contract_identifier = 'EPM-209481';
INSERT INTO property_utility (property_utility_id, property_id, utility_type_id, provider_id, contract_identifier)
SELECT 9204, 9202, utility_type_id, 9004, 'VANTI-889104' FROM utility_type WHERE code = 'GAS'
ON DUPLICATE KEY UPDATE contract_identifier = 'VANTI-889104';

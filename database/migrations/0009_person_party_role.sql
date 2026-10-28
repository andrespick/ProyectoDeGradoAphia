-- 0009: Papeles declarados de una persona (Propietario, Arrendatario, Codeudor), independientes
-- de un contrato o inmueble concreto. Permite registrar un propietario o un codeudor antes de
-- asociarlo. Reutiliza el catálogo party_role. Una persona puede tener varios papeles a la vez.

CREATE TABLE `person_party_role` (
  `person_id` BIGINT NOT NULL,
  `party_role_id` BIGINT NOT NULL,
  PRIMARY KEY (`person_id`, `party_role_id`),
  CONSTRAINT `fk_person_party_role_1` FOREIGN KEY (`person_id`) REFERENCES `person` (`person_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  KEY `ix_person_party_role_fk2` (`party_role_id`),
  CONSTRAINT `fk_person_party_role_2` FOREIGN KEY (`party_role_id`) REFERENCES `party_role` (`party_role_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

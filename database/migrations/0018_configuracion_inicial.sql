-- 0018: Valores iniciales de la política de seguridad (los del requisito original) y de los
-- datos de la empresa. Producción los necesita, por eso van en una migración y no en seeds.

INSERT INTO `security_policy`
  (`security_policy_id`, `max_failed_attempts`, `lock_minutes`, `session_hours`, `min_password_length`)
VALUES (1, 3, 15, 8, 8);

INSERT INTO `organization_profile` (`organization_profile_id`, `legal_name`) VALUES (1, 'APHIA S.A.S.');

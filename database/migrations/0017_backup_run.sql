-- 0017: Historial de respaldos. infra/production/backup/backup.sh registra cada ejecución
-- (programada o solicitada desde la web) y atiende las solicitudes pendientes. La API nunca
-- ejecuta comandos en el VPS: solo inserta la solicitud y lee el historial.

CREATE TABLE `backup_run` (
  `backup_run_id` BIGINT NOT NULL AUTO_INCREMENT,
  `trigger_type` VARCHAR(20) NOT NULL,
  `status` VARCHAR(20) NOT NULL,
  `requested_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `started_at` DATETIME(6) NULL,
  `finished_at` DATETIME(6) NULL,
  `file_name` VARCHAR(255) NULL,
  `size_bytes` BIGINT NULL,
  `remote_copy` BOOLEAN NULL,
  `error_message` VARCHAR(255) NULL,
  PRIMARY KEY (`backup_run_id`),
  KEY `ix_backup_run_status` (`status`, `backup_run_id`),
  CONSTRAINT `ck_backup_run_trigger` CHECK (trigger_type IN ('PROGRAMADO', 'MANUAL')),
  CONSTRAINT `ck_backup_run_status` CHECK (status IN ('SOLICITADO', 'EN_CURSO', 'OK', 'FALLIDO')),
  CONSTRAINT `ck_backup_run_size` CHECK (size_bytes IS NULL OR size_bytes >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;

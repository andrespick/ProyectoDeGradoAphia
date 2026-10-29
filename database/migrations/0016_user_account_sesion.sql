-- 0016: Control de sesiones y cambio obligatorio de contraseña.
-- session_version viaja en el token; al incrementarla (cerrar sesiones, restablecer o cambiar la
-- contraseña, cambiar el rol o desactivar la cuenta) los tokens emitidos dejan de valer.

ALTER TABLE `user_account`
  ADD COLUMN `session_version` INT NOT NULL DEFAULT 0,
  ADD COLUMN `must_change_password` BOOLEAN NOT NULL DEFAULT FALSE;

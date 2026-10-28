import type { Role } from "../../types/auth";

// Espejo de los grupos de apps/api/src/modules/auth/schemas.py.
export const LECTURA: readonly Role[] = ["admin_sistemas", "administrativo", "asesor"];
export const ESCRITURA: readonly Role[] = LECTURA;
export const ELIMINACION: readonly Role[] = ["admin_sistemas", "administrativo"];
export const GESTION_USUARIOS: readonly Role[] = ["admin_sistemas"];

export const NOMBRE_ROL: Record<Role, string> = {
  admin_sistemas: "Administrador de Sistemas",
  administrativo: "Administrativo",
  asesor: "Asesor",
};

export function tieneRol(roles: readonly Role[], permitidos: readonly Role[]): boolean {
  return roles.some((role) => permitidos.includes(role));
}

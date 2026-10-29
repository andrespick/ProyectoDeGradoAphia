import type { Role } from "../../types/auth";

// Espejo de los grupos de apps/api/src/modules/auth/schemas.py.
export const LECTURA: readonly Role[] = ["administrativo", "asesor"];
export const ESCRITURA: readonly Role[] = LECTURA;
export const ELIMINACION: readonly Role[] = ["administrativo"];
export const GESTION_SISTEMA: readonly Role[] = ["admin_sistemas"];
export const TODOS: readonly Role[] = [...GESTION_SISTEMA, ...LECTURA];

export const NOMBRE_ROL: Record<Role, string> = {
  admin_sistemas: "Administrador de Sistemas",
  administrativo: "Administrativo",
  asesor: "Asesor",
};

export function tieneRol(roles: readonly Role[], permitidos: readonly Role[]): boolean {
  return roles.some((role) => permitidos.includes(role));
}

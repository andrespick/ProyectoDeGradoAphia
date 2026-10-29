export type Role = "admin_sistemas" | "administrativo" | "asesor";

export interface Principal {
  sujeto: string;
  nombre: string;
  roles: Role[];
  modo: "development" | "database";
  /** Tras un restablecimiento: solo puede cambiar su contraseña. */
  debe_cambiar_clave: boolean;
}

export interface LoginResponse {
  token: string;
  expira_en: string;
  principal: Principal;
}

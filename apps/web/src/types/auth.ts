export type Role = "admin_sistemas" | "administrativo" | "asesor";

export interface Principal {
  sujeto: string;
  nombre: string;
  roles: Role[];
  modo: "development" | "database";
}

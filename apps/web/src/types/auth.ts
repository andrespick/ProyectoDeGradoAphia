export type Role = "admin" | "asesor" | "consulta";

export interface Principal {
  sujeto: string;
  nombre: string;
  roles: Role[];
  modo: "development";
}

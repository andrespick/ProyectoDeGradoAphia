import type { Page } from "./api";
import type { Role } from "./auth";

export type EstadoUsuario = "activo" | "inactivo" | "bloqueado";

export interface Usuario {
  id: number;
  usuario: string;
  nombre: string;
  tipo_identificacion: string | null;
  identificacion: string | null;
  correo: string | null;
  rol: Role;
  activo: boolean;
  bloqueada: boolean;
  bloqueada_hasta: string | null;
  intentos_fallidos: number;
  debe_cambiar_clave: boolean;
  creado_en: string;
}

export interface UsuarioCreate {
  usuario: string;
  nombre: string;
  tipo_identificacion: string;
  identificacion: string;
  correo: string;
  clave: string;
  rol: Role;
}

export interface UsuarioUpdate {
  nombre: string;
  tipo_identificacion: string;
  identificacion: string;
  correo: string;
  rol: Role;
  activo: boolean;
  clave?: string;
}

export type UsuariosPage = Page<Usuario>;

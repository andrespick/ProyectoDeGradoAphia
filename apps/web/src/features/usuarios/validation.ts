import type { Role } from "../../types/auth";
import { EMAIL_RE, type Errores } from "../shared/validation";

export const CAMPOS_USUARIO = [
  "usuario",
  "nombre",
  "tipo_identificacion",
  "identificacion",
  "correo",
  "clave",
  "rol",
] as const;

export type CampoUsuario = (typeof CAMPOS_USUARIO)[number];
export type UsuarioErrors = Errores<CampoUsuario>;

export interface UsuarioFormValues {
  usuario: string;
  nombre: string;
  tipo_identificacion: string;
  identificacion: string;
  correo: string;
  clave: string;
  rol: Role | "";
  activo: boolean;
}

const USUARIO_RE = /^[a-z0-9._-]{3,50}$/;
const IDENTIFICACION_RE = /^[A-Za-z0-9-]{3,50}$/;

export function claveValida(clave: string): boolean {
  return clave.length >= 8 && /[A-Za-z]/.test(clave) && /\d/.test(clave);
}

export function validateUsuario(values: UsuarioFormValues, modo: "crear" | "editar"): UsuarioErrors {
  const errors: UsuarioErrors = {};
  if (modo === "crear" && !USUARIO_RE.test(values.usuario)) {
    errors.usuario = "Use entre 3 y 50 caracteres: minúsculas, números, punto, guion o guion bajo.";
  }
  if (values.nombre.length < 2) errors.nombre = "Ingrese el nombre completo.";
  if (!values.tipo_identificacion) errors.tipo_identificacion = "Seleccione el tipo de identificación.";
  if (!IDENTIFICACION_RE.test(values.identificacion)) {
    errors.identificacion = "Ingrese solo letras, números o guiones (3 a 50 caracteres).";
  }
  if (!EMAIL_RE.test(values.correo)) errors.correo = "Ingrese un correo electrónico válido.";
  if (!values.rol) errors.rol = "Seleccione un rol.";
  if ((modo === "crear" || values.clave) && !claveValida(values.clave)) {
    errors.clave = "La clave debe tener al menos 8 caracteres, con letras y números.";
  }
  return errors;
}

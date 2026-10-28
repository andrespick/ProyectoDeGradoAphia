import type { ClienteCreate } from "../../types/cliente";
import { EMAIL_RE, type Errores } from "../shared/validation";

export const CAMPOS_CLIENTE = ["nombre", "correo"] as const satisfies readonly (keyof ClienteCreate)[];

export type ClienteErrors = Errores<keyof ClienteCreate>;

export function validateCliente(input: ClienteCreate): ClienteErrors {
  const errors: ClienteErrors = {};
  if (input.nombre.length < 2) errors.nombre = "El nombre debe tener al menos 2 caracteres.";
  else if (input.nombre.length > 150) errors.nombre = "El nombre admite máximo 150 caracteres.";

  if (!input.correo) errors.correo = "El correo electrónico es obligatorio.";
  else if (input.correo.length > 254 || !EMAIL_RE.test(input.correo)) {
    errors.correo = "Ingrese un correo electrónico válido.";
  }
  return errors;
}

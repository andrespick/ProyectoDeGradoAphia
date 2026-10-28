import type { ApiErrorDetail } from "../../types/api";
import type { ClienteCreate } from "../../types/cliente";

export type ClienteErrors = Partial<Record<keyof ClienteCreate, string>>;

// Validación rápida en el navegador. La validación definitiva la hace la API (Pydantic).
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

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

export function errorsFromApi(details: ApiErrorDetail[]): ClienteErrors {
  const errors: ClienteErrors = {};
  for (const detail of details) {
    if (detail.campo === "nombre" || detail.campo === "correo") {
      errors[detail.campo] = detail.mensaje.replace(/^Value error, /, "");
    }
  }
  return errors;
}

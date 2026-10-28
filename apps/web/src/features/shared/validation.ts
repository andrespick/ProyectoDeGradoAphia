import type { ApiErrorDetail } from "../../types/api";

export type Errores<T extends string> = Partial<Record<T, string>>;

// Validación rápida en el navegador. La validación definitiva la hace la API (Pydantic).
export const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/** Traduce los `detalles` de un 422 a errores por campo (solo los campos conocidos). */
export function errorsFromApi<T extends string>(
  details: ApiErrorDetail[],
  campos: readonly T[],
): Errores<T> {
  const errors: Errores<T> = {};
  for (const detail of details) {
    const campo = campos.find((c) => c === detail.campo);
    if (campo) errors[campo] = detail.mensaje.replace(/^Value error, /, "");
  }
  return errors;
}

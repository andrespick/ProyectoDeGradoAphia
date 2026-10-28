import type { Papel, Persona, PersonaCreate } from "../../types/persona";
import { EMAIL_RE, type Errores } from "../shared/validation";

export const CAMPOS_PERSONA = [
  "nombre",
  "tipo_identificacion",
  "identificacion",
  "telefono",
  "correo",
  "direccion",
  "papeles",
  "cuenta_bancaria.banco",
  "cuenta_bancaria.tipo",
  "cuenta_bancaria.numero",
] as const;

export type CampoPersona = (typeof CAMPOS_PERSONA)[number];
export type PersonaErrors = Errores<CampoPersona>;

export interface PersonaFormValues {
  nombre: string;
  tipo_identificacion: string;
  identificacion: string;
  telefono: string;
  correo: string;
  direccion: string;
  papeles: Papel[];
  conCuenta: boolean;
  banco: string;
  cuentaTipo: string;
  cuentaNumero: string;
}

const IDENTIFICACION_RE = /^[A-Za-z0-9-]{3,50}$/;
const TELEFONO_RE = /^[0-9+ ()-]{7,50}$/;
const CUENTA_RE = /^[0-9-]{1,50}$/;

export function valoresIniciales(inicial?: Persona, papelFijo: Papel | null = null): PersonaFormValues {
  return {
    nombre: inicial?.nombre ?? "",
    tipo_identificacion: inicial?.tipo_identificacion ?? "CC",
    identificacion: inicial?.identificacion ?? "",
    telefono: inicial?.telefono ?? "",
    correo: inicial?.correo ?? "",
    direccion: inicial?.direccion ?? "",
    papeles: inicial?.papeles ?? (papelFijo ? [papelFijo] : []),
    conCuenta: Boolean(inicial?.cuenta_bancaria) || papelFijo === "propietario",
    banco: inicial?.cuenta_bancaria?.banco ?? "",
    cuentaTipo: inicial?.cuenta_bancaria?.tipo ?? "",
    cuentaNumero: inicial?.cuenta_bancaria?.numero ?? "",
  };
}

/** Los propietarios exigen dirección y cuenta bancaria (requisito del cliente). */
export function validatePersona(values: PersonaFormValues, papelFijo: Papel | null): PersonaErrors {
  const errors: PersonaErrors = {};
  if (values.nombre.length < 2) errors.nombre = "Ingrese el nombre completo.";
  if (!values.tipo_identificacion) errors.tipo_identificacion = "Seleccione el tipo de identificación.";
  if (!IDENTIFICACION_RE.test(values.identificacion)) {
    errors.identificacion = "Ingrese solo letras, números o guiones (3 a 50 caracteres).";
  }
  if (values.telefono && !TELEFONO_RE.test(values.telefono)) {
    errors.telefono = "Ingrese un teléfono válido (mínimo 7 dígitos).";
  }
  if (values.correo && !EMAIL_RE.test(values.correo)) {
    errors.correo = "Ingrese un correo electrónico válido.";
  }
  if (values.papeles.length === 0) errors.papeles = "Seleccione al menos un tipo de cliente.";
  if (papelFijo === "propietario") {
    if (!values.direccion) errors.direccion = "La dirección es obligatoria para un propietario.";
    if (!values.telefono) errors.telefono = "El teléfono es obligatorio para un propietario.";
    if (!values.correo) errors.correo = "El correo es obligatorio para un propietario.";
  }
  if (values.conCuenta) {
    if (!values.banco) errors["cuenta_bancaria.banco"] = "Indique el banco.";
    if (!values.cuentaTipo) errors["cuenta_bancaria.tipo"] = "Seleccione el tipo de cuenta.";
    if (!CUENTA_RE.test(values.cuentaNumero)) {
      errors["cuenta_bancaria.numero"] = "Ingrese el número de cuenta (solo dígitos y guiones).";
    }
  }
  return errors;
}

export function aPersonaCreate(values: PersonaFormValues): PersonaCreate {
  return {
    nombre: values.nombre.trim(),
    tipo_identificacion: values.tipo_identificacion,
    identificacion: values.identificacion.trim(),
    telefono: values.telefono.trim() || null,
    correo: values.correo.trim() || null,
    direccion: values.direccion.trim() || null,
    papeles: values.papeles,
    cuenta_bancaria: values.conCuenta
      ? { banco: values.banco.trim(), tipo: values.cuentaTipo, numero: values.cuentaNumero.trim() }
      : null,
  };
}

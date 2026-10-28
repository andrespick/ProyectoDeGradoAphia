import type { Contrato, ContratoCreate } from "../../types/contrato";
import type { InmuebleResumen, PersonaResumen } from "../../types/persona";
import { normalizarDecimal } from "../../utils/formato";
import type { Errores } from "../shared/validation";

export const CAMPOS_CONTRATO = [
  "tipo",
  "inmueble_id",
  "fecha_inicio",
  "fecha_fin",
  "canon_pactado",
  "condiciones",
  "texto",
  "propietarios_ids",
  "arrendatario_id",
  "codeudores_ids",
] as const;
export type CampoContrato = (typeof CAMPOS_CONTRATO)[number];
export type ContratoErrors = Errores<CampoContrato>;

export interface ContratoFormValues {
  tipo: string;
  inmueble: InmuebleResumen | null;
  fecha_inicio: string;
  fecha_fin: string;
  canon: string;
  condiciones: string;
  texto: string;
  propietarios: PersonaResumen[];
  arrendatario: PersonaResumen | null;
  codeudores: PersonaResumen[];
}

export function valoresIniciales(inicial?: Contrato): ContratoFormValues {
  return {
    tipo: inicial?.tipo ?? "ARRENDAMIENTO",
    inmueble: inicial?.inmueble ?? null,
    fecha_inicio: inicial?.fecha_inicio ?? "",
    fecha_fin: inicial?.fecha_fin ?? "",
    canon: inicial?.canon_pactado ?? "",
    condiciones: inicial?.condiciones ?? "",
    texto: inicial?.texto ?? "",
    propietarios: inicial?.propietarios ?? [],
    arrendatario: inicial?.arrendatario ?? null,
    codeudores: inicial?.codeudores ?? [],
  };
}

export function validateContrato(values: ContratoFormValues): ContratoErrors {
  const errors: ContratoErrors = {};
  if (!values.tipo) errors.tipo = "Seleccione el tipo de contrato.";
  if (!values.inmueble) errors.inmueble_id = "Seleccione el inmueble del contrato.";
  if (!values.fecha_inicio) errors.fecha_inicio = "Ingrese la fecha de inicio.";
  if (values.fecha_fin && values.fecha_inicio && values.fecha_fin < values.fecha_inicio) {
    errors.fecha_fin = "La fecha de fin no puede ser anterior a la de inicio.";
  }
  if (normalizarDecimal(values.canon) === "NaN") {
    errors.canon_pactado = "Ingrese el canon en pesos, con máximo dos decimales (p. ej. 1.500.000).";
  }
  if (values.propietarios.length === 0) errors.propietarios_ids = "Asocie al menos un propietario.";
  if (values.arrendatario && values.codeudores.some((c) => c.id === values.arrendatario?.id)) {
    errors.codeudores_ids = "El arrendatario no puede ser también codeudor del contrato.";
  }
  return errors;
}

export function aContratoCreate(values: ContratoFormValues): ContratoCreate {
  return {
    tipo: values.tipo,
    inmueble_id: values.inmueble?.id ?? 0,
    fecha_inicio: values.fecha_inicio,
    fecha_fin: values.fecha_fin || null,
    canon_pactado: normalizarDecimal(values.canon),
    condiciones: values.condiciones.trim() || null,
    texto: values.texto.trim() || null,
    propietarios_ids: values.propietarios.map((p) => p.id),
    arrendatario_id: values.arrendatario?.id ?? null,
    codeudores_ids: values.codeudores.map((c) => c.id),
  };
}

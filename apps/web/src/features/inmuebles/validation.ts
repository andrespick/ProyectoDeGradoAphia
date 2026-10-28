import type { Inmueble, InmuebleCreate, ServicioPublicoCreate } from "../../types/inmueble";
import type { PersonaResumen } from "../../types/persona";
import { normalizarDecimal } from "../../utils/formato";
import type { Errores } from "../shared/validation";

export const CAMPOS_INMUEBLE = ["direccion", "ciudad", "matricula", "canon", "estado", "servicios", "propietarios_ids"] as const;
export type CampoInmueble = (typeof CAMPOS_INMUEBLE)[number];
export type InmuebleErrors = Errores<CampoInmueble>;

export interface ServicioFormValues {
  tipo: string;
  proveedor: string;
  numero_contrato: string;
}

export interface InmuebleFormValues {
  direccion: string;
  ciudad: string;
  matricula: string;
  canon: string;
  estado: string;
  servicios: ServicioFormValues[];
  propietarios: PersonaResumen[];
}

export function valoresIniciales(inicial?: Inmueble): InmuebleFormValues {
  return {
    direccion: inicial?.direccion ?? "",
    ciudad: inicial?.ciudad ?? "",
    matricula: inicial?.matricula ?? "",
    canon: inicial?.canon ?? "",
    estado: inicial?.estado ?? "DISPONIBLE",
    servicios: (inicial?.servicios ?? []).map((s) => ({
      tipo: s.tipo ?? "",
      proveedor: s.proveedor ?? "",
      numero_contrato: s.numero_contrato,
    })),
    propietarios: inicial?.propietarios ?? [],
  };
}

export function validateInmueble(values: InmuebleFormValues): InmuebleErrors {
  const errors: InmuebleErrors = {};
  if (values.direccion.trim().length < 3) errors.direccion = "Ingrese la dirección del inmueble.";
  if (normalizarDecimal(values.canon) === "NaN") {
    errors.canon = "Ingrese el canon en pesos, con máximo dos decimales (p. ej. 1.500.000).";
  }
  if (values.propietarios.length === 0) errors.propietarios_ids = "Asocie al menos un propietario.";
  if (values.servicios.some((s) => !s.numero_contrato.trim())) {
    errors.servicios = "Cada servicio público necesita su número de contrato.";
  }
  return errors;
}

export function aInmuebleCreate(values: InmuebleFormValues): InmuebleCreate {
  const servicios: ServicioPublicoCreate[] = values.servicios.map((s) => ({
    tipo: s.tipo || null,
    proveedor: s.proveedor.trim() || null,
    numero_contrato: s.numero_contrato.trim(),
  }));
  return {
    direccion: values.direccion.trim(),
    ciudad: values.ciudad.trim() || null,
    matricula: values.matricula.trim() || null,
    canon: normalizarDecimal(values.canon),
    estado: values.estado || null,
    servicios,
    propietarios_ids: values.propietarios.map((p) => p.id),
  };
}

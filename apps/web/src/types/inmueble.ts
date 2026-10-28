import type { Page } from "./api";
import type { PersonaResumen } from "./persona";

export interface ServicioPublicoCreate {
  tipo: string | null;
  proveedor: string | null;
  numero_contrato: string;
}

export interface ServicioPublico extends ServicioPublicoCreate {
  id: number;
}

export interface Inmueble {
  id: number;
  direccion: string;
  ciudad: string | null;
  matricula: string | null;
  /** Decimal serializado como cadena ("1500000.00"). */
  canon: string | null;
  moneda: string | null;
  estado: string | null;
  servicios: ServicioPublico[];
  propietarios: PersonaResumen[];
  total_contratos: number;
}

export interface InmuebleCreate {
  direccion: string;
  ciudad: string | null;
  matricula: string | null;
  canon: string | null;
  estado: string | null;
  servicios: ServicioPublicoCreate[];
  propietarios_ids: number[];
}

export type InmueblesPage = Page<Inmueble>;

export const NOMBRE_ESTADO: Record<string, string> = { DISPONIBLE: "Disponible", OCUPADO: "Ocupado" };
export const BADGE_ESTADO: Record<string, string> = { DISPONIBLE: "badge-warn", OCUPADO: "badge-ok" };

import type { Page } from "./api";
import type { ContratoResumen, InmuebleResumen, PersonaResumen } from "./persona";

export type EstadoContrato = "programado" | "vigente" | "finalizado";
/** Filtro «Por vencer» de la API: contratos que terminan en los próximos 60 días. */
export const DIAS_POR_VENCER = 60;

export interface ContratoListado {
  id: number;
  tipo: string;
  inmueble: InmuebleResumen;
  fecha_inicio: string;
  fecha_fin: string | null;
  /** Decimal serializado como cadena ("1500000.00"). */
  canon_pactado: string | null;
  moneda: string | null;
  estado: EstadoContrato;
  dias_restantes: number | null;
  propietarios: PersonaResumen[];
  arrendatario: PersonaResumen | null;
  codeudores: PersonaResumen[];
}

export interface Contrato extends ContratoListado {
  condiciones: string | null;
  texto: string | null;
}

export interface ContratoCreate {
  tipo: string;
  inmueble_id: number;
  fecha_inicio: string;
  fecha_fin: string | null;
  canon_pactado: string | null;
  condiciones: string | null;
  texto: string | null;
  propietarios_ids: number[];
  arrendatario_id: number | null;
  codeudores_ids: number[];
}

export type ContratosPage = Page<ContratoListado>;

export interface ResultadosBusqueda {
  personas: PersonaResumen[];
  inmuebles: InmuebleResumen[];
  contratos: ContratoResumen[];
}

export const NOMBRE_TIPO: Record<string, string> = { ARRENDAMIENTO: "Arrendamiento", ADMINISTRACION: "Administración" };

export function etiquetaEstado(contrato: Pick<ContratoListado, "estado" | "dias_restantes">): {
  texto: string;
  badge: string;
} {
  if (contrato.estado === "finalizado") return { texto: "Finalizado", badge: "badge-muted" };
  if (contrato.estado === "programado") return { texto: "Programado", badge: "badge-info" };
  if (contrato.dias_restantes !== null && contrato.dias_restantes <= DIAS_POR_VENCER) {
    return { texto: "Por vencer", badge: "badge-warn" };
  }
  return { texto: "Vigente", badge: "badge-ok" };
}

import type { Page } from "./api";

export type Papel = "propietario" | "arrendatario" | "codeudor";

export const PAPELES: readonly Papel[] = ["propietario", "arrendatario", "codeudor"];
export const NOMBRE_PAPEL: Record<Papel, string> = {
  propietario: "Propietario",
  arrendatario: "Arrendatario",
  codeudor: "Codeudor",
};
export const BADGE_PAPEL: Record<Papel, string> = {
  propietario: "badge-primary",
  arrendatario: "badge-ok",
  codeudor: "badge-info",
};

export interface CuentaBancariaCreate {
  banco: string;
  tipo: string;
  numero: string;
}

export interface CuentaBancaria extends CuentaBancariaCreate {
  id: number;
}

/** Lo mínimo para mostrar una persona dentro de otro registro (inmueble, contrato). */
export interface PersonaResumen {
  id: number;
  nombre: string;
  tipo_identificacion: string | null;
  identificacion: string | null;
  telefono: string | null;
  correo: string | null;
}

export interface Persona extends PersonaResumen {
  direccion: string | null;
  papeles: Papel[];
  cuenta_bancaria: CuentaBancaria | null;
  total_inmuebles: number;
}

export interface PersonaCreate {
  nombre: string;
  tipo_identificacion: string;
  identificacion: string;
  telefono: string | null;
  correo: string | null;
  direccion: string | null;
  papeles: Papel[];
  cuenta_bancaria: CuentaBancariaCreate | null;
}

export interface InmuebleResumen {
  id: number;
  direccion: string;
  ciudad: string | null;
  estado: string | null;
}

export interface ContratoResumen {
  id: number;
  tipo: string;
  fecha_inicio: string;
  fecha_fin: string | null;
  inmueble: InmuebleResumen;
}

export interface PersonaDetalle extends Persona {
  inmuebles: InmuebleResumen[];
  contratos_como_propietario: ContratoResumen[];
  contratos_como_arrendatario: ContratoResumen[];
  contratos_como_codeudor: ContratoResumen[];
  usuario: string | null;
}

export type PersonasPage = Page<Persona>;

export function identificacionDe(persona: PersonaResumen): string {
  return [persona.tipo_identificacion, persona.identificacion].filter(Boolean).join(" ") || "—";
}

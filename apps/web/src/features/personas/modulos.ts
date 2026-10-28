import { KeyRound, type LucideIcon, ShieldCheck, Users } from "lucide-react";

import type { Papel } from "../../types/persona";

export interface ModuloPersonas {
  titulo: string;
  singular: string;
  plural: string;
  ruta: string;
  api: string;
  papelFijo: Papel | null;
  filtros: readonly string[];
  descripcion: string;
  icon: LucideIcon;
}

/** Las tres pantallas comparten servicio, formulario y tabla; solo cambia esta configuración. */
export const MODULOS = {
  clientes: {
    titulo: "Gestión de clientes",
    singular: "cliente",
    plural: "clientes",
    ruta: "/clientes",
    api: "/api/v1/clientes",
    papelFijo: null,
    filtros: ["q", "papel"],
    descripcion: "Directorio de arrendatarios, propietarios y codeudores vinculados a inmuebles y contratos.",
    icon: Users,
  },
  propietarios: {
    titulo: "Gestión de propietarios",
    singular: "propietario",
    plural: "propietarios",
    ruta: "/propietarios",
    api: "/api/v1/propietarios",
    papelFijo: "propietario",
    filtros: ["q", "correo"],
    descripcion: "Titulares de inmuebles, con su cuenta bancaria y los inmuebles que administramos.",
    icon: KeyRound,
  },
  codeudores: {
    titulo: "Gestión de codeudores",
    singular: "codeudor",
    plural: "codeudores",
    ruta: "/codeudores",
    api: "/api/v1/codeudores",
    papelFijo: "codeudor",
    filtros: ["q", "contrato_id"],
    descripcion: "Deudores solidarios que respaldan los contratos de arrendamiento.",
    icon: ShieldCheck,
  },
} as const satisfies Record<string, ModuloPersonas>;

export type Modulo = keyof typeof MODULOS;

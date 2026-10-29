import type { Page } from "./api";

// Tipos de las pantallas del Administrador de Sistemas (sistema, auditoría, configuración,
// catálogos y papelera). Espejo de los esquemas de apps/api/src/modules/{sistema,auditoria,...}.

export interface PoliticaSeguridad {
  max_intentos: number;
  minutos_bloqueo: number;
  horas_sesion: number;
  largo_minimo_clave: number;
}

export type PoliticaPublica = Omit<PoliticaSeguridad, "horas_sesion">;

export interface Empresa {
  nombre: string;
  nit: string | null;
  direccion: string | null;
  ciudad: string | null;
  telefono: string | null;
  correo: string | null;
}

export interface EventoAuditoria {
  id: number;
  fecha: string;
  actor_id: number | null;
  actor_nombre: string | null;
  actor_usuario: string | null;
  accion: string;
  entidad: string | null;
  entidad_id: number | null;
  detalle: string | null;
  request_id: string | null;
}

export type EstadoRespaldo = "solicitado" | "en_curso" | "ok" | "fallido";

export interface Respaldo {
  id: number;
  origen: "programado" | "manual";
  estado: EstadoRespaldo;
  solicitado_en: string;
  iniciado_en: string | null;
  terminado_en: string | null;
  archivo: string | null;
  tamano_bytes: number | null;
  copia_externa: boolean | null;
  error: string | null;
}

export interface EstadoSistema {
  api: { version: string; entorno: string; runtime: "workers" | "asgi" };
  base_de_datos: {
    disponible: boolean;
    latencia_ms: number | null;
    version: string | null;
    tamano_bytes: number | null;
  };
  migraciones: { aplicadas: number; ultima: string | null; aplicada_en: string | null } | null;
  registros: {
    personas: number;
    inmuebles: number;
    contratos: number;
    usuarios: number;
    eventos_auditoria: number;
    en_papelera: number;
  } | null;
  respaldos: { ultimo_exitoso: Respaldo | null; pendiente: Respaldo | null; atrasado: boolean } | null;
}

export type CatalogoAdministrable =
  | "tipos-identificacion"
  | "tipos-contrato"
  | "tipos-cuenta-bancaria"
  | "tipos-servicio"
  | "ciudades"
  | "bancos"
  | "proveedores-servicios";

export interface ItemCatalogo {
  id: number;
  codigo: string | null;
  nombre: string;
  en_uso: number;
}

export type TipoRegistro = "persona" | "inmueble" | "contrato";

export interface RegistroEliminado {
  id: number;
  tipo: TipoRegistro;
  entidad_id: number;
  descripcion: string;
  eliminado_en: string;
  eliminado_por: string | null;
}

export type AuditoriaPage = Page<EventoAuditoria>;
export type RespaldosPage = Page<Respaldo>;
export type PapeleraPage = Page<RegistroEliminado>;

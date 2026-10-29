import type { CatalogoAdministrable, EstadoRespaldo, TipoRegistro } from "../../types/administracion";

/** Acciones que registran los routers de la API en la auditoría. */
export const ACCIONES: Record<string, string> = {
  inicio_sesion: "Inicio de sesión",
  inicio_sesion_fallido: "Intento fallido",
  cuenta_bloqueada: "Cuenta bloqueada",
  cambio_clave: "Cambio de contraseña",
  crear: "Creación",
  actualizar: "Modificación",
  eliminar: "Eliminación",
  restaurar: "Restauración",
  eliminar_definitivo: "Eliminación definitiva",
  desbloquear: "Desbloqueo",
  restablecer_clave: "Clave restablecida",
  cerrar_sesiones: "Sesiones cerradas",
  solicitar_respaldo: "Respaldo solicitado",
};

export const ENTIDADES: Record<string, string> = {
  usuario: "Usuario",
  persona: "Persona",
  inmueble: "Inmueble",
  contrato: "Contrato",
  catalogo: "Catálogo",
  politica_seguridad: "Política de seguridad",
  empresa: "Datos de la empresa",
  respaldo: "Respaldo",
  papelera: "Papelera",
};

export const TIPOS_REGISTRO: Record<TipoRegistro, string> = {
  persona: "Persona",
  inmueble: "Inmueble",
  contrato: "Contrato",
};

interface DefCatalogo {
  value: CatalogoAdministrable;
  label: string;
  conCodigo: boolean;
}

export const CATALOGO_INICIAL: DefCatalogo = {
  value: "tipos-identificacion",
  label: "Tipos de identificación",
  conCodigo: true,
};

export const CATALOGOS: readonly DefCatalogo[] = [
  CATALOGO_INICIAL,
  { value: "tipos-contrato", label: "Tipos de contrato", conCodigo: true },
  { value: "tipos-cuenta-bancaria", label: "Tipos de cuenta", conCodigo: true },
  { value: "tipos-servicio", label: "Servicios públicos", conCodigo: true },
  { value: "ciudades", label: "Ciudades", conCodigo: false },
  { value: "bancos", label: "Bancos", conCodigo: false },
  { value: "proveedores-servicios", label: "Proveedores", conCodigo: false },
];

export const ESTADO_RESPALDO: Record<EstadoRespaldo, { label: string; badge: string }> = {
  solicitado: { label: "Solicitado", badge: "badge-info" },
  en_curso: { label: "En curso", badge: "badge-warn" },
  ok: { label: "Completado", badge: "badge-ok" },
  fallido: { label: "Fallido", badge: "badge-error" },
};

export interface Resumen {
  personas: { total: number; propietarios: number; arrendatarios: number; codeudores: number };
  inmuebles: { total: number; ocupados: number; disponibles: number };
  contratos: {
    total: number;
    vigentes: number;
    por_vencer_30: number;
    por_vencer_60: number;
    finalizados: number;
    codeudores_vinculados: number;
  };
  usuarios: { total: number; activos: number; bloqueados: number };
}

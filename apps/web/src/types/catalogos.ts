export interface Opcion {
  codigo: string;
  nombre: string;
}

export interface Ciudad {
  id: number;
  nombre: string;
}

export interface Catalogos {
  tipos_identificacion: Opcion[];
  papeles: Opcion[];
  roles: Opcion[];
  estados_ocupacion: Opcion[];
  tipos_contrato: Opcion[];
  tipos_cuenta_bancaria: Opcion[];
  tipos_servicio: Opcion[];
  monedas: Opcion[];
  ciudades: Ciudad[];
  bancos: string[];
  proveedores_servicios: string[];
}

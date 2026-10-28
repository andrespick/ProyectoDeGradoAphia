export interface Cliente {
  id: number;
  nombre: string;
  correo: string;
  creado_en: string;
  actualizado_en: string;
}

export interface ClienteCreate {
  nombre: string;
  correo: string;
}

export interface ClientesPage {
  items: Cliente[];
  total: number;
  limit: number;
  offset: number;
}

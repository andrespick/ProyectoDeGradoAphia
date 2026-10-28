import type { Cliente, ClienteCreate, ClientesPage } from "../types/cliente";
import { apiRequest } from "./apiClient";

export function listClientes(
  params: { limit?: number; offset?: number } = {},
  signal?: AbortSignal,
): Promise<ClientesPage> {
  const query = new URLSearchParams({
    limit: String(params.limit ?? 20),
    offset: String(params.offset ?? 0),
  });
  return apiRequest<ClientesPage>(`/api/v1/clientes?${query.toString()}`, { signal });
}

export function createCliente(input: ClienteCreate): Promise<Cliente> {
  return apiRequest<Cliente>("/api/v1/clientes", { method: "POST", body: input });
}

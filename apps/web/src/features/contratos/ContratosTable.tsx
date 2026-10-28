import { Eye, Pencil, Trash2 } from "lucide-react";
import { Link } from "react-router";

import { type ContratoListado, etiquetaEstado, NOMBRE_TIPO } from "../../types/contrato";
import { formatearFecha, formatearMoneda } from "../../utils/formato";

interface ContratosTableProps {
  items: ContratoListado[];
  loading: boolean;
  error: string | null;
  puedeEditar: boolean;
  puedeEliminar: boolean;
  onRetry: () => void;
  onEliminar: (contrato: ContratoListado) => void;
}

export function diasRestantesTexto(dias: number | null): string {
  if (dias === null) return "Indefinido";
  if (dias === 0) return "Vence hoy";
  return `${dias} día${dias === 1 ? "" : "s"} restante${dias === 1 ? "" : "s"}`;
}

export function ContratosTable({
  items,
  loading,
  error,
  puedeEditar,
  puedeEliminar,
  onRetry,
  onEliminar,
}: ContratosTableProps) {
  if (error) {
    return (
      <div className="alert alert-error" role="alert">
        <p>{error}</p>
        <button type="button" className="secondary" onClick={onRetry}>
          Reintentar
        </button>
      </div>
    );
  }
  if (loading && items.length === 0) {
    return (
      <p className="muted" role="status">
        Cargando contratos…
      </p>
    );
  }
  if (items.length === 0) {
    return <p className="empty-state">No hay contratos que coincidan con la búsqueda.</p>;
  }
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th scope="col">Nº y vigencia</th>
            <th scope="col">Inmueble</th>
            <th scope="col">Partes</th>
            <th scope="col">Codeudores</th>
            <th scope="col" className="num">
              Canon
            </th>
            <th scope="col">Estado</th>
            <th scope="col">
              <span className="visually-hidden">Acciones</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {items.map((contrato) => {
            const estado = etiquetaEstado(contrato);
            const nombre = `contrato ${contrato.id}`;
            return (
              <tr key={contrato.id}>
                <td className="nowrap">
                  <span className="cell-title">
                    #{contrato.id} · {NOMBRE_TIPO[contrato.tipo] ?? contrato.tipo}
                  </span>
                  <span className="cell-sub">
                    {formatearFecha(contrato.fecha_inicio)} – {contrato.fecha_fin ? formatearFecha(contrato.fecha_fin) : "indefinido"}
                  </span>
                  {contrato.estado !== "finalizado" && contrato.fecha_fin && (
                    <span className="cell-sub">{diasRestantesTexto(contrato.dias_restantes)}</span>
                  )}
                </td>
                <td>
                  <span className="cell-title">{contrato.inmueble.direccion}</span>
                  <span className="cell-sub">{contrato.inmueble.ciudad ?? "Sin ciudad"}</span>
                </td>
                <td>
                  <span className="cell-sub">Propietario(s): {contrato.propietarios.map((p) => p.nombre).join(", ") || "—"}</span>
                  <span className="cell-sub">Arrendatario: {contrato.arrendatario?.nombre ?? "—"}</span>
                </td>
                <td>
                  <span className="chip-list">
                    {contrato.codeudores.length === 0 && <span className="muted">—</span>}
                    {contrato.codeudores.map((c) => (
                      <span key={c.id} className="chip">
                        {c.nombre}
                      </span>
                    ))}
                  </span>
                </td>
                <td className="num">{formatearMoneda(contrato.canon_pactado)}</td>
                <td>
                  <span className={`badge ${estado.badge}`}>{estado.texto}</span>
                </td>
                <td>
                  <span className="row-actions">
                    <Link to={`/contratos/${contrato.id}`} aria-label={`Ver ${nombre}`}>
                      <Eye size={16} aria-hidden="true" /> Ver
                    </Link>
                    {puedeEditar && (
                      <Link to={`/contratos/${contrato.id}/editar`} aria-label={`Editar ${nombre}`}>
                        <Pencil size={16} aria-hidden="true" /> Editar
                      </Link>
                    )}
                    {puedeEliminar && (
                      <button
                        type="button"
                        className="danger"
                        aria-label={`Eliminar ${nombre}`}
                        onClick={() => onEliminar(contrato)}
                      >
                        <Trash2 size={16} aria-hidden="true" /> Eliminar
                      </button>
                    )}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

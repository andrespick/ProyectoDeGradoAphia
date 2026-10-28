interface PaginationProps {
  total: number;
  limit: number;
  offset: number;
  onOffsetChange: (offset: number) => void;
  onLimitChange?: (limit: number) => void;
  /** Sustantivo plural para «Mostrando 1–20 de 57 registros». */
  etiqueta?: string;
}

const TAMANOS = [10, 20, 50];

export function Pagination({
  total,
  limit,
  offset,
  onOffsetChange,
  onLimitChange,
  etiqueta = "registros",
}: PaginationProps) {
  const desde = total === 0 ? 0 : offset + 1;
  const hasta = Math.min(offset + limit, total);
  const tamanos = TAMANOS.includes(limit) ? TAMANOS : [...TAMANOS, limit].sort((a, b) => a - b);
  return (
    <nav className="pagination" aria-label="Paginación">
      <p className="muted">
        Mostrando {desde}–{hasta} de {total} {etiqueta}
      </p>
      <div className="pagination-controls">
        {onLimitChange && (
          <label className="pagination-size">
            Por página
            <select value={limit} onChange={(event) => onLimitChange(Number(event.target.value))}>
              {tamanos.map((size) => (
                <option key={size} value={size}>
                  {size}
                </option>
              ))}
            </select>
          </label>
        )}
        <button
          type="button"
          className="secondary"
          disabled={offset === 0}
          onClick={() => onOffsetChange(Math.max(0, offset - limit))}
        >
          Anterior
        </button>
        <button
          type="button"
          className="secondary"
          disabled={hasta >= total}
          onClick={() => onOffsetChange(offset + limit)}
        >
          Siguiente
        </button>
      </div>
    </nav>
  );
}

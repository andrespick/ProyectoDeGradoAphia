import type { ReactNode } from "react";
import { Link } from "react-router";

interface KpiCardProps {
  etiqueta: string;
  valor: ReactNode;
  detalle?: ReactNode;
  icono?: ReactNode;
  tono?: "neutro" | "ok" | "warn" | "error" | "info";
  to?: string;
}

/** Tarjeta de indicador: etiqueta en mayúsculas, cifra grande y detalle. */
export function KpiCard({ etiqueta, valor, detalle, icono, tono = "neutro", to }: KpiCardProps) {
  const content = (
    <>
      <div className="kpi-top">
        <span className="kpi-label">{etiqueta}</span>
        {icono && (
          <span className={`icon-box icon-box-${tono}`} aria-hidden="true">
            {icono}
          </span>
        )}
      </div>
      <p className={`kpi-value kpi-value-${tono}`}>{valor}</p>
      {detalle && <p className="kpi-detail">{detalle}</p>}
    </>
  );
  if (to) {
    return (
      <Link to={to} className="kpi kpi-link">
        {content}
      </Link>
    );
  }
  return <article className="kpi">{content}</article>;
}

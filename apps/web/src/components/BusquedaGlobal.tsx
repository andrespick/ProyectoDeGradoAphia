import { Search } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router";

import { buscarGlobal } from "../services/contratosService";
import { NOMBRE_TIPO, type ResultadosBusqueda } from "../types/contrato";
import { formatearFecha } from "../utils/formato";

interface Resultado {
  clave: string;
  to: string;
  titulo: string;
  detalle: string;
}

function aplanar(r: ResultadosBusqueda): { grupo: string; items: Resultado[] }[] {
  return [
    {
      grupo: "Personas",
      items: r.personas.map((p) => ({
        clave: `p${p.id}`,
        to: `/clientes/${p.id}`,
        titulo: p.nombre,
        detalle: [p.tipo_identificacion, p.identificacion].filter(Boolean).join(" "),
      })),
    },
    {
      grupo: "Inmuebles",
      items: r.inmuebles.map((i) => ({
        clave: `i${i.id}`,
        to: `/inmuebles/${i.id}/editar`,
        titulo: i.direccion,
        detalle: i.ciudad ?? "",
      })),
    },
    {
      grupo: "Contratos",
      items: r.contratos.map((c) => ({
        clave: `c${c.id}`,
        to: `/contratos/${c.id}`,
        titulo: `Contrato #${c.id} · ${NOMBRE_TIPO[c.tipo] ?? c.tipo}`,
        detalle: `${c.inmueble.direccion} · ${formatearFecha(c.fecha_inicio)}`,
      })),
    },
  ].filter((g) => g.items.length > 0);
}

/** Caja de búsqueda de la barra superior: personas, inmuebles y contratos (`GET /api/v1/buscar`). */
export function BusquedaGlobal() {
  const [q, setQ] = useState("");
  const [grupos, setGrupos] = useState<ReturnType<typeof aplanar> | null>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const raiz = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setQ("");
    setGrupos(null);
  }, [location.pathname]);

  useEffect(() => {
    const texto = q.trim();
    if (texto.length < 2) {
      setGrupos(null);
      return;
    }
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      buscarGlobal(texto, controller.signal)
        .then((r) => setGrupos(aplanar(r)))
        .catch(() => {
          if (!controller.signal.aborted) setGrupos([]);
        });
    }, 250);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [q]);

  const primero = grupos?.[0]?.items[0];

  return (
    <div
      className="busqueda-global"
      ref={raiz}
      onBlur={(event) => {
        if (!raiz.current?.contains(event.relatedTarget as Node | null)) setGrupos(null);
      }}
    >
      <label className="topbar-search">
        <Search size={18} aria-hidden="true" />
        <input
          type="search"
          value={q}
          placeholder="Buscar inmueble, cliente, contrato…"
          aria-label="Búsqueda global"
          autoComplete="off"
          onChange={(event) => setQ(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Escape") {
              setQ("");
              setGrupos(null);
            }
            if (event.key === "Enter" && primero) navigate(primero.to);
          }}
        />
      </label>
      {grupos && (
        <div className="busqueda-resultados" role="region" aria-label="Resultados de búsqueda">
          {grupos.length === 0 && <p className="muted">Sin resultados.</p>}
          {grupos.map((grupo) => (
            <div key={grupo.grupo}>
              <p className="busqueda-grupo">{grupo.grupo}</p>
              <ul>
                {grupo.items.map((item) => (
                  <li key={item.clave}>
                    <Link to={item.to}>
                      <strong>{item.titulo}</strong>
                      {item.detalle && <span className="muted"> · {item.detalle}</span>}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

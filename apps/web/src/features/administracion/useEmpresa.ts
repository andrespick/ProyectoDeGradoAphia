import { useEffect, useState } from "react";

import { getEmpresa } from "../../services/administracionService";
import type { Empresa } from "../../types/administracion";

/** Datos de la empresa para el pie de página y la impresión; `null` mientras cargan o si fallan. */
export function useEmpresa(activo = true): Empresa | null {
  const [empresa, setEmpresa] = useState<Empresa | null>(null);

  useEffect(() => {
    if (!activo) return;
    let vigente = true;
    getEmpresa()
      .then((datos) => {
        if (vigente) setEmpresa(datos);
      })
      .catch(() => undefined); // dato decorativo: sin él se muestra el nombre por defecto
    return () => {
      vigente = false;
    };
  }, [activo]);

  return empresa;
}

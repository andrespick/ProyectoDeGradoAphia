import { CircleHelp } from "lucide-react";
import { Link } from "react-router";

/** Enlace a la sección de la ayuda en línea que corresponde a la pantalla actual. */
export function AyudaLink({ seccion, etiqueta }: { seccion: string; etiqueta: string }) {
  return (
    <Link to={`/ayuda#${seccion}`} className="button-link ghost ayuda-link" aria-label={`Ayuda sobre ${etiqueta}`}>
      <CircleHelp size={18} aria-hidden="true" /> Ayuda
    </Link>
  );
}

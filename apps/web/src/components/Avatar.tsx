interface AvatarProps {
  nombre: string;
  tono?: "neutro" | "primary" | "ok" | "info";
}

export function iniciales(nombre: string): string {
  const partes = nombre.trim().split(/\s+/).filter(Boolean);
  const primera = partes[0]?.[0] ?? "";
  const segunda = partes.length > 1 ? (partes[partes.length - 1]?.[0] ?? "") : (partes[0]?.[1] ?? "");
  return `${primera}${segunda}`.toUpperCase() || "?";
}

/** Círculo con las iniciales de una persona (sin fotos: el modelo no las guarda). */
export function Avatar({ nombre, tono = "neutro" }: AvatarProps) {
  return (
    <span className={`avatar avatar-${tono}`} aria-hidden="true">
      {iniciales(nombre)}
    </span>
  );
}

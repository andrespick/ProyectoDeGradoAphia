const moneda = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  maximumFractionDigits: 0,
});
const fecha = new Intl.DateTimeFormat("es-CO", { dateStyle: "medium", timeZone: "UTC" });

/** "1500000.50" → "$ 1.500.001" (pesos colombianos sin decimales). */
export function formatearMoneda(valor: string | number | null | undefined): string {
  if (valor === null || valor === undefined || valor === "") return "—";
  const numero = typeof valor === "number" ? valor : Number(valor);
  return Number.isNaN(numero) ? String(valor) : moneda.format(numero);
}

/** Fechas de la API (YYYY-MM-DD o ISO) → "28 oct 2026". */
export function formatearFecha(valor: string | null | undefined): string {
  if (!valor) return "—";
  return fecha.format(new Date(valor.length === 10 ? `${valor}T00:00:00Z` : valor));
}

/** Normaliza lo escrito en un campo de dinero ("1.500.000,50" o "1500000.50") a "1500000.50". */
export function normalizarDecimal(texto: string): string | null {
  const limpio = texto.trim().replace(/\s|\$/g, "");
  if (!limpio) return null;
  const sinMiles = /^\d{1,3}(\.\d{3})+(,\d{1,2})?$/.test(limpio)
    ? limpio.replace(/\./g, "").replace(",", ".")
    : limpio.replace(",", ".");
  return /^\d{1,10}(\.\d{1,2})?$/.test(sinMiles) ? sinMiles : "NaN";
}

const fechaHora = new Intl.DateTimeFormat("es-CO", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: "America/Bogota",
});

/** Instantes de la API (ISO en UTC) → "28 oct 2026, 3:15 p. m." en hora de Colombia. */
export function formatearFechaHora(valor: string | null | undefined): string {
  return valor ? fechaHora.format(new Date(valor)) : "—";
}

/** 2097152 → "2,0 MB". */
export function formatearBytes(valor: number | null | undefined): string {
  if (valor === null || valor === undefined) return "—";
  const unidades = ["B", "KB", "MB", "GB"];
  let n = valor;
  let i = 0;
  while (n >= 1024 && i < unidades.length - 1) {
    n /= 1024;
    i += 1;
  }
  return `${n.toLocaleString("es-CO", { maximumFractionDigits: i === 0 ? 0 : 1, minimumFractionDigits: i === 0 ? 0 : 1 })} ${unidades[i]}`;
}

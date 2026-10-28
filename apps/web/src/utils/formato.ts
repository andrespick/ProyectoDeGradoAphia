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

export const eur = (v: number | string | null | undefined, digits = 0) =>
  v == null || v === ""
    ? "–"
    : new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR", maximumFractionDigits: digits, minimumFractionDigits: digits }).format(Number(v));

export const num = (v: number | null | undefined, digits = 0) =>
  v == null || Number.isNaN(v) ? "–" : new Intl.NumberFormat("de-DE", { maximumFractionDigits: digits, minimumFractionDigits: digits }).format(v);

export const pct = (v: number | null | undefined, digits = 0) => (v == null || Number.isNaN(v) ? "–" : `${num(v, digits)} %`);

export const secs = (v: number | null | undefined) => {
  if (v == null) return "–";
  if (v < 90) return `${num(v, 0)} s`;
  return `${Math.floor(v / 60)} min ${Math.round(v % 60)} s`;
};

export const when = (iso: string | null | undefined) =>
  iso ? new Intl.DateTimeFormat("de-DE", { dateStyle: "short", timeStyle: "short" }).format(new Date(iso)) : "–";

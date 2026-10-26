const nf = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 });

export const mw = (v) => (v == null ? "–" : nf.format(Math.round(v)));
export const signedMw = (v) =>
  v == null ? "–" : `${v > 0 ? "+" : v < 0 ? "−" : ""}${nf.format(Math.abs(Math.round(v)))}`;
export const pct = (v, d = 1) => (v == null ? "–" : `${v.toFixed(d)}%`);

// All times in the data are UTC (== UK local time in January).
export const hhmm = (iso) => iso.slice(11, 16);

export function longDate(isoDate) {
  const d = new Date(`${isoDate}T00:00:00Z`);
  return d.toLocaleDateString("en-GB", {
    weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "UTC",
  });
}

export function shortDate(isoDate) {
  const d = new Date(`${isoDate}T00:00:00Z`);
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });
}

export function dateTime(iso) {
  const d = new Date(iso);
  const day = d.toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });
  return `${day}, ${hhmm(d.toISOString())} UTC`;
}

export function addDays(isoDate, n) {
  const d = new Date(`${isoDate}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}
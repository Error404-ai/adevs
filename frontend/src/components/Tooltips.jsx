import { mw, signedMw } from "../format.js";

// Generic tooltip for the accuracy charts: one row per series.
export function MwTooltip({ active, payload, label, labelPrefix = "", signedKeys = [] }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="tip">
      <strong>{labelPrefix}{label}</strong>
      {payload.map((p) => (
        <div className="tip-row" key={p.dataKey}>
          <span>{p.name}</span>
          <span>
            {signedKeys.includes(p.dataKey) ? signedMw(p.value) : mw(p.value)} MW
          </span>
        </div>
      ))}
    </div>
  );
}

// Tooltip for the forecast-vs-actual chart: reads the whole row.
export function DecisionTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const r = payload[0].payload;
  const err = r.actual != null ? r.forecast - r.actual : null;
  return (
    <div className="tip">
      <strong>{r.time} UTC</strong>
      <div className="tip-row"><span>Forecast</span><span>{mw(r.forecast)} MW</span></div>
      {r.band && (
        <div className="tip-row">
          <span>Likely range</span>
          <span>{mw(r.band[0])} – {mw(r.band[1])} MW</span>
        </div>
      )}
      <div className="tip-row"><span>Actual</span><span>{mw(r.actual)} MW</span></div>
      {err != null && (
        <div className="tip-row"><span>Error</span><span>{signedMw(err)} MW</span></div>
      )}
    </div>
  );
}
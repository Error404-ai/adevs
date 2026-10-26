import { useEffect, useMemo, useState } from "react";
import {
  Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, XAxis, YAxis, Tooltip,
} from "recharts";
import { getJSON } from "../api.js";
import { addDays, dateTime, hhmm, longDate, mw, signedMw } from "../format.js";
import Panel from "../components/Panel.jsx";
import StatStrip from "../components/StatStrip.jsx";
import Legend from "../components/Legend.jsx";
import { DecisionTooltip } from "../components/Tooltips.jsx";

const COLORS = { forecast: "#1D6FD1", actual: "#0F2233", band: "#1D6FD1" };

export default function DecisionView({ config, date, setDate, cutoff }) {
  const [state, setState] = useState({ data: null, error: null, loading: true });

  useEffect(() => {
    let alive = true;
    setState((s) => ({ ...s, loading: true, error: null }));
    getJSON("/api/forecast-at-decision", { delivery_date: date, cutoff_hour: cutoff })
      .then((data) => alive && setState({ data, error: null, loading: false }))
      .catch((e) => alive && setState({ data: null, error: e.message, loading: false }));
    return () => { alive = false; };
  }, [date, cutoff]);

  const { data, error, loading } = state;

  const view = useMemo(() => {
    if (!data) return null;
    const rows = data.rows.map((r) => ({
      time: hhmm(r.startTime),
      forecast: r.forecast,
      actual: r.actual,
      band: r.band_low != null ? [r.band_low, r.band_high] : null,
      publishTime: r.publishTime,
    }));
    const avg = (k) => rows.reduce((a, r) => a + r[k], 0) / rows.length;
    const peak = rows.reduce((a, r) => (r.forecast > a.forecast ? r : a));
    const low = rows.reduce((a, r) => (r.forecast < a.forecast ? r : a));
    const withBand = rows.filter((r) => r.band);
    const bandLow = withBand.length ? withBand.reduce((a, r) => a + r.band[0], 0) / withBand.length : null;
    const bandHigh = withBand.length ? withBand.reduce((a, r) => a + r.band[1], 0) / withBand.length : null;
    const pubs = [...new Set(rows.map((r) => r.publishTime))].sort();
    return {
      rows, peak, low, bandLow, bandHigh, hasBand: withBand.length > 0,
      avgForecast: avg("forecast"), avgActual: avg("actual"),
      firstPub: pubs[0], lastPub: pubs[pubs.length - 1],
    };
  }, [data]);

  const canPrev = date > config.first_delivery;
  const canNext = date < config.last_delivery;

  return (
    <>
      <div className="controls">
        <div className="field">
          <label htmlFor="delivery">Delivery day</label>
          <div className="date-ctl">
            <button type="button" aria-label="Previous day" disabled={!canPrev}
                    onClick={() => setDate(addDays(date, -1))}>‹</button>
            <input id="delivery" type="date" value={date}
                   min={config.first_delivery} max={config.last_delivery}
                   onChange={(e) => {
                     const v = e.target.value;
                     if (v >= config.first_delivery && v <= config.last_delivery) setDate(v);
                   }} />
            <button type="button" aria-label="Next day" disabled={!canNext}
                    onClick={() => setDate(addDays(date, 1))}>›</button>
          </div>
        </div>
        {data && (
          <p className="muted decision-line">
            Order placed {dateTime(data.decision_time)}, the day before delivery.
          </p>
        )}
      </div>

      {error && <p className="error" role="alert">Could not load this day: {error}</p>}

      {view && (
        <div className={loading ? "dim" : ""}>
          <div className="lede">
            <h1>
              {longDate(date)}: the forecast available at decision time
              averages {mw(view.avgForecast)} MW of wind.
            </h1>
            <p>
              {view.hasBand ? (
                <>
                  Hour by hour, the likely range of actual output averages{" "}
                  <b>{mw(view.bandLow)}</b> to <b>{mw(view.bandHigh)} MW</b>. That range comes from the middle
                  80% of forecast errors seen so far this month. Over those {data.error_band.history_days} completed
                  days the forecast has run <b>{mw(Math.abs(data.error_band.bias))} MW</b>{" "}
                  {data.error_band.bias >= 0 ? "too high" : "too low"} on average.
                </>
              ) : (
                <>
                  There is not yet enough history for an error range: it needs at least three
                  completed days of forecast errors that were known before this decision.
                </>
              )}
            </p>
            <p className="muted small">
              Built from forecast{view.firstPub === view.lastPub ? "" : "s"} published{" "}
              {view.firstPub === view.lastPub
                ? dateTime(view.firstPub)
                : `${dateTime(view.firstPub)} to ${dateTime(view.lastPub)}`}
              , the latest available before the order.
            </p>
          </div>

          <StatStrip items={[
            { label: "Average forecast", value: mw(view.avgForecast), unit: "MW" },
            { label: "Highest forecast", value: mw(view.peak.forecast), unit: "MW", hint: `at ${view.peak.time}` },
            { label: "Lowest forecast", value: mw(view.low.forecast), unit: "MW", hint: `at ${view.low.time}` },
            { label: "Actual average", value: mw(view.avgActual), unit: "MW", hint: "what was generated" },
            {
              label: "Forecast error", unit: "MW",
              value: signedMw(data.day_metrics.bias),
              tone: data.day_metrics.bias > 0 ? "over" : "under",
              hint: data.day_metrics.bias > 0 ? "forecast was too high" : "forecast was too low",
            },
          ]} />

          <Panel>
            <Legend items={[
              { label: "Forecast", color: COLORS.forecast },
              { label: "Actual", color: COLORS.actual },
              ...(view.hasBand ? [{ label: "Likely range of actual output", color: COLORS.band, kind: "area" }] : []),
            ]} />
            <div className="chart tall">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={view.rows} margin={{ top: 8, right: 16, bottom: 4, left: 4 }}>
                  <CartesianGrid stroke="#E3E8ED" vertical={false} />
                  <XAxis dataKey="time" interval={5} tickLine={false} axisLine={{ stroke: "#B9C4CE" }}
                         tick={{ fill: "#5B6B7B", fontSize: 12 }} />
                  <YAxis domain={[0, (m) => Math.ceil(m / 2000) * 2000]} tickLine={false} axisLine={false}
                         width={56} tick={{ fill: "#5B6B7B", fontSize: 12 }}
                         tickFormatter={(v) => mw(v)}
                         label={{ value: "MW", position: "insideTopLeft", offset: -4, fill: "#5B6B7B", fontSize: 12 }} />
                  <Tooltip content={<DecisionTooltip />} />
                  {view.hasBand && (
                    <Area dataKey="band" stroke="none" fill={COLORS.band} fillOpacity={0.14}
                          isAnimationActive={false} activeDot={false} />
                  )}
                  <Line dataKey="forecast" name="Forecast" stroke={COLORS.forecast} strokeWidth={2.5}
                        dot={false} isAnimationActive={false} />
                  <Line dataKey="actual" name="Actual" stroke={COLORS.actual} strokeWidth={2}
                        dot={false} isAnimationActive={false} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
            <p className="muted small chart-note">
              Times are UTC (the same as UK time in January). The shaded range is the forecast adjusted by the middle 80%
              of earlier forecast errors (10th to 90th percentile).
            </p>
          </Panel>

          <details className="table-wrap">
            <summary>Half-hourly values ({view.rows.length} rows)</summary>
            <div className="scroll">
              <table>
                <thead>
                  <tr><th>Time (UTC)</th><th>Forecast</th><th>Likely range</th><th>Actual</th><th>Error</th></tr>
                </thead>
                <tbody>
                  {view.rows.map((r) => (
                    <tr key={r.time}>
                      <td>{r.time}</td>
                      <td>{mw(r.forecast)}</td>
                      <td>{r.band ? `${mw(r.band[0])} – ${mw(r.band[1])}` : "–"}</td>
                      <td>{mw(r.actual)}</td>
                      <td>{signedMw(r.forecast - r.actual)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </div>
      )}

      {!view && loading && <p className="muted">Loading forecast…</p>}
    </>
  );
}
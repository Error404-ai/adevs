import { useEffect, useMemo, useState } from "react";
import {
  Bar, BarChart, CartesianGrid, Cell, Line, ComposedChart, ReferenceLine,
  ResponsiveContainer, XAxis, YAxis, Tooltip,
} from "recharts";
import { getJSON } from "../api.js";
import { mw, pct, shortDate, signedMw } from "../format.js";
import Panel from "../components/Panel.jsx";
import StatStrip from "../components/StatStrip.jsx";
import Legend from "../components/Legend.jsx";
import { MwTooltip } from "../components/Tooltips.jsx";

const OVER = "#C03A2B";   // forecast higher than actual
const UNDER = "#2A8C82";  // forecast lower than actual
const MISS = "#8493A3";   // average miss (MAE)
const tick = { fill: "#5B6B7B", fontSize: 12 };
const signColor = (v) => (v >= 0 ? OVER : UNDER);

const biasLegend = [
  { label: "Forecast too high", color: OVER, kind: "box" },
  { label: "Forecast too low", color: UNDER, kind: "box" },
];

export default function AccuracyView({ cutoff }) {
  const [state, setState] = useState({ data: null, error: null });

  useEffect(() => {
    let alive = true;
    setState({ data: null, error: null });
    Promise.all([
      getJSON("/api/metrics", { cutoff_hour: cutoff }),
      getJSON("/api/error-by-horizon"),
      getJSON("/api/error-by-hour", { cutoff_hour: cutoff }),
      getJSON("/api/error-by-level", { cutoff_hour: cutoff }),
    ])
      .then(([metrics, horizon, hour, level]) =>
        alive && setState({ data: { metrics, horizon, hour, level }, error: null }))
      .catch((e) => alive && setState({ data: null, error: e.message }));
    return () => { alive = false; };
  }, [cutoff]);

  const { data, error } = state;

  const derived = useMemo(() => {
    if (!data) return null;
    const { overall, daily } = data.metrics;
    const over = daily.filter((d) => d.bias > 0).length;
    const worstHour = data.hour.reduce((a, r) => (r.bias > a.bias ? r : a));
    const worstLevel = data.level.reduce((a, r) => (r.bias > a.bias ? r : a));
    return { overall, daily, over, worstHour, worstLevel,
             hFirst: data.horizon[0], hLast: data.horizon[data.horizon.length - 1] };
  }, [data]);

  if (error) return <p className="error" role="alert">Could not load accuracy figures: {error}</p>;
  if (!derived) return <p className="muted">Loading accuracy figures…</p>;

  const { overall: o, daily, over, worstHour, worstLevel, hFirst, hLast } = derived;
  const dir = o.bias >= 0 ? "above" : "below";

  return (
    <>
      <div className="lede">
        <h1>
          Over January, the day-ahead wind forecast ran {mw(Math.abs(o.bias))} MW
          ({pct(Math.abs(o.bias_pct_of_actual))}) {dir} what was generated.
        </h1>
        <p>
          It was {o.bias >= 0 ? "too high" : "too low"} on <b>{o.bias >= 0 ? over : daily.length - over} of {daily.length}</b> delivery days. If that average bias were
          removed, the typical miss would fall from <b>{mw(o.mae)}</b> to <b>{mw(o.mae_bias_removed)} MW</b>:
          about {Math.round((1 - o.mae_bias_removed / o.mae) * 100)}% of the typical miss is a steady bias
          that can be planned for.
        </p>
        <p className="muted small">
          Each figure compares the forecast available at decision time with the wind actually generated,
          for every half-hour of 2 January to 1 February 2026 ({o.n.toLocaleString("en-GB")} points).
          Error is forecast minus actual, so a positive number means the forecast was too high.
        </p>
      </div>

      <StatStrip items={[
        { label: "Average miss (MAE)", value: mw(o.mae), unit: "MW", hint: "typical size of the error" },
        { label: "Large-error miss (RMSE)", value: mw(o.rmse), unit: "MW", hint: "weights big misses more" },
        { label: "Average bias", value: signedMw(o.bias), unit: "MW",
          tone: o.bias > 0 ? "over" : "under", hint: `${pct(o.bias_pct_of_actual)} of actual output` },
        { label: "Bad-case miss (P90)", value: mw(o.p90_abs_error), unit: "MW",
          hint: "9 in 10 half-hours miss by less" },
      ]} />

      <div className="grid-2">
        <Panel title={o.bias >= 0
                 ? `Too high on ${over} of ${daily.length} days`
                 : `Too low on ${daily.length - over} of ${daily.length} days`}
               note="Average forecast error for each delivery day (MW).">
          <Legend items={biasLegend} />
          <div className="chart">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={daily} margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
                <CartesianGrid stroke="#E3E8ED" vertical={false} />
                <XAxis dataKey="date" tickFormatter={shortDate} interval={4} tickLine={false}
                       axisLine={{ stroke: "#B9C4CE" }} tick={tick} />
                <YAxis tickLine={false} axisLine={false} width={52} tick={tick} tickFormatter={mw} />
                <ReferenceLine y={0} stroke="#0F2233" />
                <Tooltip content={<MwTooltip labelPrefix="" signedKeys={["bias"]} />}
                         labelFormatter={shortDate} />
                <Bar dataKey="bias" name="Average error" isAnimationActive={false}>
                  {daily.map((d) => <Cell key={d.date} fill={signColor(d.bias)} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title={`Largest over-forecast is around ${String(worstHour.hour).padStart(2, "0")}:00 (${signedMw(worstHour.bias)} MW)`}
               note="Average error by hour of the delivery day, UTC.">
          <Legend items={[...biasLegend, { label: "Average miss", color: MISS }]} />
          <div className="chart">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={data.hour} margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
                <CartesianGrid stroke="#E3E8ED" vertical={false} />
                <XAxis dataKey="hour" tickFormatter={(h) => String(h).padStart(2, "0")} interval={2}
                       tickLine={false} axisLine={{ stroke: "#B9C4CE" }} tick={tick} />
                <YAxis tickLine={false} axisLine={false} width={52} tick={tick} tickFormatter={mw} />
                <ReferenceLine y={0} stroke="#0F2233" />
                <Tooltip content={<MwTooltip labelPrefix="Hour " signedKeys={["bias"]} />} />
                <Bar dataKey="bias" name="Bias" isAnimationActive={false}>
                  {data.hour.map((r) => <Cell key={r.hour} fill={signColor(r.bias)} />)}
                </Bar>
                <Line dataKey="mae" name="Average miss" stroke={MISS} strokeWidth={2}
                      dot={false} isAnimationActive={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title={`Average miss: ${mw(hFirst.mae)} MW for forecasts published ${hFirst.bucket} ahead, ${mw(hLast.mae)} MW at ${hLast.bucket} ahead`}
               note="Error by how long before delivery the forecast was published (all forecasts, not only the one used for the order).">
          <Legend items={[{ label: "Average miss", color: MISS, kind: "box" }, ...biasLegend]} />
          <div className="chart">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.horizon} margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
                <CartesianGrid stroke="#E3E8ED" vertical={false} />
                <XAxis dataKey="bucket" tickLine={false} axisLine={{ stroke: "#B9C4CE" }} tick={tick} />
                <YAxis tickLine={false} axisLine={false} width={52} tick={tick} tickFormatter={mw} />
                <ReferenceLine y={0} stroke="#0F2233" />
                <Tooltip content={<MwTooltip labelPrefix="Published " signedKeys={["bias"]} />} />
                <Bar dataKey="mae" name="Average miss" fill={MISS} isAnimationActive={false} />
                <Bar dataKey="bias" name="Bias" isAnimationActive={false}>
                  {data.horizon.map((r) => <Cell key={r.bucket} fill={signColor(r.bias)} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title={`Over-forecast is largest in ${worstLevel.level} wind (${signedMw(worstLevel.bias)} MW)`}
               note="Error split into four equal groups by how much wind was actually generated.">
          <Legend items={[{ label: "Average miss", color: MISS, kind: "box" }, ...biasLegend]} />
          <div className="chart">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.level.map((r) => ({ ...r, label: `${r.level} wind` }))}
                        margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
                <CartesianGrid stroke="#E3E8ED" vertical={false} />
                <XAxis dataKey="label" tickLine={false} axisLine={{ stroke: "#B9C4CE" }} tick={tick} />
                <YAxis tickLine={false} axisLine={false} width={52} tick={tick} tickFormatter={mw} />
                <ReferenceLine y={0} stroke="#0F2233" />
                <Tooltip content={<MwTooltip signedKeys={["bias"]} />} />
                <Bar dataKey="mae" name="Average miss" fill={MISS} isAnimationActive={false} />
                <Bar dataKey="bias" name="Bias" isAnimationActive={false}>
                  {data.level.map((r) => <Cell key={r.level} fill={signColor(r.bias)} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="muted small chart-note">
            Output ranges: {data.level.map((r) => `${r.level} ${r.range_mw} MW`).join(" · ")}
          </p>
        </Panel>
      </div>
    </>
  );
}
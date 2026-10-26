import { useEffect, useState } from "react";
import { getJSON } from "./api.js";
import DecisionView from "./views/DecisionView.jsx";
import AccuracyView from "./views/AccuracyView.jsx";

const CUTOFFS = [6, 7, 8, 9, 10, 11, 12];

export default function App() {
  const [config, setConfig] = useState(null);
  const [error, setError] = useState(null);
  const [view, setView] = useState("decision");
  const [date, setDate] = useState(null);
  const [cutoff, setCutoff] = useState(9);

  useEffect(() => {
    getJSON("/api/config")
      .then((c) => {
        setConfig(c);
        setCutoff(c.default_cutoff_hour_utc);
        // Open on a mid-month day: it has a full error history behind it.
        setDate("2026-01-15");
      })
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="page">
      <header className="top">
        <div>
          <p className="brand">Wind forecast review</p>
          <p className="muted small">GB national wind · day-ahead purchasing · January 2026</p>
        </div>
        <div className="field cutoff">
          <label htmlFor="cutoff">Order placed at</label>
          <select id="cutoff" value={cutoff} onChange={(e) => setCutoff(Number(e.target.value))}>
            {CUTOFFS.map((h) => (
              <option key={h} value={h}>{String(h).padStart(2, "0")}:00 UTC</option>
            ))}
          </select>
        </div>
      </header>

      <nav className="tabs" role="tablist" aria-label="Views">
        <button role="tab" aria-selected={view === "decision"}
                onClick={() => setView("decision")}>Decision view</button>
        <button role="tab" aria-selected={view === "accuracy"}
                onClick={() => setView("accuracy")}>Forecast accuracy</button>
      </nav>

      <main>
        {error && (
          <p className="error" role="alert">
            Could not reach the data service: {error}. Check that the backend is running on port 8000.
          </p>
        )}
        {config && date && view === "decision" && (
          <DecisionView config={config} date={date} setDate={setDate} cutoff={cutoff} />
        )}
        {config && view === "accuracy" && <AccuracyView cutoff={cutoff} />}
        {!config && !error && <p className="muted">Loading…</p>}
      </main>

      <footer className="foot muted small">
        Data: Elexon BMRS. Forecasts from WINDFOR, actual generation from FUELHH (fuel type WIND),
        both national level. Times are UTC.
      </footer>
    </div>
  );
}
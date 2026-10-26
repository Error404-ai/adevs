// A single ruled strip of figures (not a grid of separate cards).
export default function StatStrip({ items }) {
  return (
    <dl className="stat-strip">
      {items.map((s) => (
        <div className="stat" key={s.label}>
          <dt>{s.label}</dt>
          <dd className={s.tone ? `tone-${s.tone}` : ""}>
            {s.value}
            {s.unit && <span className="unit"> {s.unit}</span>}
          </dd>
          {s.hint && <p className="hint">{s.hint}</p>}
        </div>
      ))}
    </dl>
  );
}
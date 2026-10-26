export default function Legend({ items }) {
  return (
    <ul className="legend">
      {items.map((i) => (
        <li key={i.label}>
          <span className={`swatch ${i.kind || "line"}`} style={{ "--c": i.color }} />
          {i.label}
        </li>
      ))}
    </ul>
  );
}
export default function Panel({ title, note, children, className = "" }) {
  return (
    <section className={`panel ${className}`}>
      {(title || note) && (
        <header className="panel-head">
          {title && <h2>{title}</h2>}
          {note && <p className="muted">{note}</p>}
        </header>
      )}
      {children}
    </section>
  );
}
function MetricCard({ label, value, unit, hint }) {
  const display = value == null || value === '' ? '—' : value

  return (
    <article className="rounded-lg border border-line bg-white px-4 py-4 shadow-sm">
      <p className="text-xs font-medium tracking-wide text-muted uppercase">{label}</p>
      <p className="mt-2 flex items-baseline gap-1.5">
        <span className="text-2xl font-semibold tracking-tight text-ink">{display}</span>
        {display !== '—' && unit ? (
          <span className="text-sm text-muted">{unit}</span>
        ) : null}
      </p>
      {hint ? <p className="mt-1 text-xs leading-5 text-muted">{hint}</p> : null}
    </article>
  )
}

export default MetricCard

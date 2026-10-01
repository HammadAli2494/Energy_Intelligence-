function StatCard({ label, value, hint }) {
  return (
    <article className="rounded-xl border border-line bg-white p-5">
      <p className="text-xs font-medium tracking-wide text-muted uppercase">{label}</p>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-ink">{value}</p>
      {hint ? <p className="mt-1 text-xs leading-5 text-muted">{hint}</p> : null}
    </article>
  )
}

export default StatCard

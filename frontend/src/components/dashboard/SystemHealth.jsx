function statusLabel(mongodb) {
  if (mongodb === 'connected') return 'Connected'
  if (mongodb === 'unavailable') return 'Unavailable'
  if (mongodb === 'not_configured') return 'Not configured'
  return '—'
}

function Dot({ ok }) {
  return (
    <span
      className={`inline-block h-1.5 w-1.5 rounded-full ${ok ? 'bg-brand' : 'bg-stone-400'}`}
      aria-hidden="true"
    />
  )
}

function SystemHealth({ health, compact = false }) {
  if (!health) {
    return compact ? (
      <p className="text-xs text-muted">System health unavailable</p>
    ) : (
      <p className="text-sm text-muted">System health is currently unavailable.</p>
    )
  }

  const apiOnline = Boolean(health.status)
  const modelLoaded = Boolean(health.model_loaded)
  const dbConnected = health.mongodb === 'connected'

  if (compact) {
    return (
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted">
        <span className="inline-flex items-center gap-1.5">
          <Dot ok={apiOnline} />
          {apiOnline ? 'API Online' : 'API Offline'}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <Dot ok={modelLoaded} />
          {modelLoaded ? 'Model Loaded' : 'Model Not loaded'}
        </span>
      </div>
    )
  }

  return (
    <section className="rounded-lg border border-line bg-white px-4 py-3 text-sm">
      <h2 className="text-xs font-medium tracking-wide text-muted uppercase">System Health</h2>
      <ul className="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-muted">
        <li className="inline-flex items-center gap-1.5">
          <Dot ok={apiOnline} />
          API {apiOnline ? 'Online' : 'Offline'}
        </li>
        <li className="inline-flex items-center gap-1.5">
          <Dot ok={modelLoaded} />
          Model {modelLoaded ? 'Loaded' : 'Not loaded'}
        </li>
        <li className="inline-flex items-center gap-1.5">
          <Dot ok={dbConnected} />
          Database {statusLabel(health.mongodb)}
        </li>
      </ul>
    </section>
  )
}

export default SystemHealth

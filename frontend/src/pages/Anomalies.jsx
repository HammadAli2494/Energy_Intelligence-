import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Disclaimer from '../components/common/Disclaimer'
import ErrorState from '../components/common/ErrorState'
import LoadingSpinner from '../components/common/LoadingSpinner'
import PageHeader from '../components/common/PageHeader'
import SeverityBadge from '../components/common/SeverityBadge'
import { getAnomalies } from '../services/api'
import { formatMw, formatTimestamp } from '../utils/format'

function Anomalies() {
  const [payload, setPayload] = useState(null)
  const [severity, setSeverity] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    getAnomalies({ severity: severity || undefined, limit: 50 })
      .then((data) => {
        if (!cancelled) {
          setPayload(data)
          setError('')
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [severity])

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Residuals"
        title="Anomalies"
        description="Hours where |actual − predicted| is large relative to 2019 validation MAE."
      />
      <Disclaimer>
        An anomaly here means unusual consumption relative to the forecast. It is not
        proof of equipment failure or a grid incident.
      </Disclaimer>

      {payload ? (
        <p className="text-sm leading-6 text-muted">
          {payload.rule} Showing {payload.items.length} of {payload.total} flagged hours.
        </p>
      ) : null}

      <div className="flex flex-wrap gap-2">
        {[
          { value: '', label: 'All' },
          { value: 'high', label: 'High' },
          { value: 'medium', label: 'Medium' },
        ].map((option) => (
          <button
            key={option.value || 'all'}
            type="button"
            onClick={() => setSeverity(option.value)}
            className={`rounded-md px-3 py-1.5 text-sm ${
              severity === option.value
                ? 'bg-brand text-white'
                : 'border border-line bg-white text-ink'
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>

      {loading ? <LoadingSpinner label="Loading anomalies" /> : null}
      {error ? <ErrorState title="Could not load anomalies" message={error} /> : null}

      {payload && !loading ? (
        <div className="overflow-x-auto rounded-xl border border-line bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-line bg-canvas text-xs tracking-wide text-muted uppercase">
              <tr>
                <th className="px-4 py-3 font-medium">Hour (UTC)</th>
                <th className="px-4 py-3 font-medium">Actual</th>
                <th className="px-4 py-3 font-medium">Predicted</th>
                <th className="px-4 py-3 font-medium">|Residual|</th>
                <th className="px-4 py-3 font-medium">Severity</th>
              </tr>
            </thead>
            <tbody>
              {payload.items.map((item) => (
                <tr key={item.id} className="border-b border-line last:border-0">
                  <td className="px-4 py-3">
                    <Link
                      to={`/anomalies/${encodeURIComponent(item.id)}`}
                      className="font-medium text-brand hover:text-brand-dark"
                    >
                      {formatTimestamp(item.utc_timestamp)}
                    </Link>
                  </td>
                  <td className="px-4 py-3">{formatMw(item.actual_load_mw, 0)}</td>
                  <td className="px-4 py-3">{formatMw(item.predicted_load_mw, 0)}</td>
                  <td className="px-4 py-3">{formatMw(item.abs_residual_mw, 1)}</td>
                  <td className="px-4 py-3">
                    <SeverityBadge severity={item.severity} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  )
}

export default Anomalies

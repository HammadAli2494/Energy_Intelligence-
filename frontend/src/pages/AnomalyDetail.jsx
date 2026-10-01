import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import Disclaimer from '../components/common/Disclaimer'
import ErrorState from '../components/common/ErrorState'
import LoadingSpinner from '../components/common/LoadingSpinner'
import PageHeader from '../components/common/PageHeader'
import SeverityBadge from '../components/common/SeverityBadge'
import StatCard from '../components/common/StatCard'
import { getAnomaly } from '../services/api'
import { formatMw, formatTimestamp } from '../utils/format'

function AnomalyDetail() {
  const { anomalyId } = useParams()
  const [item, setItem] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    getAnomaly(anomalyId)
      .then((data) => {
        if (!cancelled) {
          setItem(data)
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
  }, [anomalyId])

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Anomaly"
        title="Residual detail"
        description="One flagged hour compared with the saved one-hour-ahead model."
      />
      <Disclaimer>
        Large residuals can come from holidays, COVID-year demand shifts, weather
        mismatch, or model error. They are not a diagnosis.
      </Disclaimer>
      <Link to="/anomalies" className="text-sm font-medium text-brand hover:text-brand-dark">
        Back to anomalies
      </Link>

      {loading ? <LoadingSpinner label="Loading anomaly" /> : null}
      {error ? <ErrorState title="Anomaly not found" message={error} /> : null}

      {item ? (
        <>
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold text-ink">
              {formatTimestamp(item.utc_timestamp)}
            </h2>
            <SeverityBadge severity={item.severity} />
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard label="Actual load" value={formatMw(item.actual_load_mw, 1)} />
            <StatCard label="Predicted load" value={formatMw(item.predicted_load_mw, 1)} />
            <StatCard
              label="Residual"
              value={formatMw(item.residual_mw, 1)}
              hint={`Absolute ${formatMw(item.abs_residual_mw, 1)}`}
            />
          </div>
          <p className="text-sm leading-6 text-muted">{item.note}</p>
        </>
      ) : null}
    </div>
  )
}

export default AnomalyDetail

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import AnomalyChart from '../components/charts/AnomalyChart'
import ForecastChart from '../components/charts/ForecastChart'
import MetricCard from '../components/dashboard/MetricCard'
import ModelPerformanceCard from '../components/dashboard/ModelPerformanceCard'
import RecentForecasts from '../components/dashboard/RecentForecasts'
import SystemHealth from '../components/dashboard/SystemHealth'
import WeatherContext from '../components/dashboard/WeatherContext'
import ErrorState from '../components/common/ErrorState'
import LoadingSpinner from '../components/common/LoadingSpinner'
import SeverityBadge from '../components/common/SeverityBadge'
import { getDashboardSummary, getHealth, getRecentForecasts } from '../services/api'
import { formatTimestamp } from '../utils/format'

function kpiValue(value, digits = 0) {
  if (value == null || Number.isNaN(Number(value))) return null
  return Number(value).toLocaleString('en-US', {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  })
}

function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [recent, setRecent] = useState(null)
  const [health, setHealth] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    Promise.all([getDashboardSummary(), getRecentForecasts(8), getHealth()])
      .then(([dashboard, forecasts, status]) => {
        if (!cancelled) {
          setSummary(dashboard)
          setRecent(forecasts)
          setHealth(status)
          setError('')
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || 'Forecast data is currently unavailable.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-3 border-b border-line pb-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-ink">
            Energy Intelligence Dashboard
          </h1>
          <p className="mt-1 text-sm text-muted">
            Energy demand forecasting and anomaly monitoring
          </p>
        </div>
        <SystemHealth health={health} compact />
      </header>

      {loading ? <LoadingSpinner label="Loading dashboard" /> : null}
      {error ? (
        <ErrorState title="Forecast data is currently unavailable." message={error} />
      ) : null}

      {summary ? (
        <>
          <p className="text-xs text-muted">{summary.dataset_note}</p>

          <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="Latest Demand"
              value={kpiValue(summary.latest_demand_mw, 0)}
              unit="MW"
              hint={formatTimestamp(summary.latest_utc)}
            />
            <MetricCard
              label="Next-Hour Forecast"
              value={kpiValue(summary.next_hour?.predicted_load_mw, 0)}
              unit="MW"
              hint={
                summary.next_hour
                  ? formatTimestamp(summary.next_hour.utc_timestamp)
                  : 'Unavailable'
              }
            />
            <MetricCard
              label="Model MAE"
              value={kpiValue(summary.valid_mae_mw, 2)}
              unit="MW"
              hint="2019 validation, selected model"
            />
            <MetricCard
              label="Detected Anomalies"
              value={kpiValue(summary.anomalies_last_7_days, 0)}
              hint={`${kpiValue(summary.anomalies_total, 0) ?? '—'} in the full modeled series`}
            />
          </section>

          <section className="rounded-lg border border-line bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center justify-between gap-3">
              <h2 className="text-base font-semibold text-ink">Actual vs Forecast Energy Demand</h2>
              <Link to="/forecast" className="text-sm font-medium text-brand hover:text-brand-dark">
                Forecast detail
              </Link>
            </div>
            <ForecastChart data={summary.recent_history || []} />
          </section>

          <section className="grid gap-4 lg:grid-cols-5">
            <article className="rounded-lg border border-line bg-white p-4 shadow-sm lg:col-span-3">
              <h2 className="text-base font-semibold text-ink">Anomaly Monitoring</h2>
              <p className="mt-1 text-xs leading-5 text-muted">
                Anomalies indicate observations where actual demand deviates significantly from
                the model forecast.
              </p>
              <div className="mt-3">
                <AnomalyChart data={summary.recent_history || []} />
              </div>
            </article>
            <article className="rounded-lg border border-line bg-white p-4 shadow-sm lg:col-span-2">
              <div className="flex items-center justify-between gap-2">
                <h2 className="text-base font-semibold text-ink">Recent Anomalies</h2>
                <Link to="/anomalies" className="text-sm font-medium text-brand hover:text-brand-dark">
                  All
                </Link>
              </div>
              {summary.recent_anomalies?.length ? (
                <ul className="mt-3 divide-y divide-line text-sm">
                  {summary.recent_anomalies.map((item) => (
                    <li key={item.utc_timestamp} className="py-2">
                      <div className="flex items-start justify-between gap-2">
                        <Link
                          to={`/anomalies/${encodeURIComponent(item.utc_timestamp.replace('+00:00', 'Z'))}`}
                          className="font-medium text-ink hover:text-brand"
                        >
                          {formatTimestamp(item.utc_timestamp)}
                        </Link>
                        <SeverityBadge severity={item.severity} />
                      </div>
                      <p className="mt-1 text-xs text-muted">
                        Actual {kpiValue(item.actual_load_mw, 0)} MW · Forecast{' '}
                        {kpiValue(item.predicted_load_mw, 0)} MW · |Dev|{' '}
                        {kpiValue(item.abs_residual_mw, 1)} MW
                      </p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-3 text-sm text-muted">No flagged hours in this window.</p>
              )}
            </article>
          </section>

          <section className="rounded-lg border border-line bg-white p-4 shadow-sm">
            <h2 className="text-base font-semibold text-ink">Recent Forecasts</h2>
            <div className="mt-3">
              <RecentForecasts rows={recent?.items} source={recent?.source} />
            </div>
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <article className="rounded-lg border border-line bg-white p-4 shadow-sm">
              <h2 className="text-base font-semibold text-ink">Weather Context</h2>
              <div className="mt-3">
                <WeatherContext weather={summary.weather} />
              </div>
            </article>
            <article className="rounded-lg border border-line bg-white p-4 shadow-sm">
              <h2 className="text-base font-semibold text-ink">Model Performance</h2>
              <div className="mt-3">
                <ModelPerformanceCard performance={summary.model_performance} />
              </div>
            </article>
          </section>

          <SystemHealth health={health} />
        </>
      ) : null}
    </div>
  )
}

export default Dashboard

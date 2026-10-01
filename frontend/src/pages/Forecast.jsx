import { useEffect, useState } from 'react'
import DemandChart from '../components/charts/DemandChart'
import Disclaimer from '../components/common/Disclaimer'
import ErrorState from '../components/common/ErrorState'
import LoadingSpinner from '../components/common/LoadingSpinner'
import PageHeader from '../components/common/PageHeader'
import StatCard from '../components/common/StatCard'
import { createForecast, getEnergyHistory, getLatestForecast } from '../services/api'
import { formatMw, formatNumber, formatTimestamp } from '../utils/format'

function Forecast() {
  const [latest, setLatest] = useState(null)
  const [history, setHistory] = useState([])
  const [nextHour, setNextHour] = useState(null)
  const [error, setError] = useState('')
  const [actionError, setActionError] = useState('')
  const [loading, setLoading] = useState(true)
  const [predicting, setPredicting] = useState(false)

  useEffect(() => {
    let cancelled = false
    Promise.all([getLatestForecast(), getEnergyHistory(168)])
      .then(([forecast, series]) => {
        if (!cancelled) {
          setLatest(forecast)
          setHistory(series.items || [])
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
  }, [])

  function runNextHour() {
    setPredicting(true)
    setActionError('')
    createForecast()
      .then((payload) => setNextHour(payload))
      .catch((err) => setActionError(err.message))
      .finally(() => setPredicting(false))
  }

  const point = latest?.forecast

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Inference"
        title="Forecast"
        description="The saved Histogram Gradient Boosting model predicts one hour ahead. Training does not run in the API."
      />
      <Disclaimer>
        These are model estimates for an educational project, not operational dispatch
        instructions. The series ends in September 2020.
      </Disclaimer>

      {loading ? <LoadingSpinner label="Loading forecast" /> : null}
      {error ? <ErrorState title="Could not load forecast" message={error} /> : null}

      {point ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Last known hour"
            value={formatMw(point.actual_load_mw, 0)}
            hint={formatTimestamp(point.utc_timestamp)}
          />
          <StatCard
            label="Predicted for that hour"
            value={formatMw(point.predicted_load_mw, 0)}
            hint={latest.model}
          />
          <StatCard
            label="Residual"
            value={formatMw(point.residual_mw, 1)}
            hint="Predicted minus actual"
          />
          <StatCard
            label="Madrid weather (t−1)"
            value={`${formatNumber(point.temperature_c, 1)} °C`}
            hint={`${formatNumber(point.relative_humidity_pct, 0)}% humidity`}
          />
        </div>
      ) : null}

      <section className="rounded-xl border border-line bg-white p-5">
        <h2 className="text-base font-semibold text-ink">Last 168 hours</h2>
        <p className="mt-1 text-sm text-muted">{latest?.note}</p>
        <div className="mt-4">
          <DemandChart data={history} />
        </div>
      </section>

      <section className="rounded-xl border border-line bg-white p-5">
        <h2 className="text-base font-semibold text-ink">Next hour after the dataset</h2>
        <p className="mt-1 text-sm leading-6 text-muted">
          Uses lags and last-known weather from the final published load hour. There is
          no actual load to compare against for this step.
        </p>
        <button
          type="button"
          onClick={runNextHour}
          disabled={predicting}
          className="mt-4 rounded-md bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-60"
        >
          {predicting ? 'Predicting…' : 'Predict next hour'}
        </button>
        {actionError ? (
          <div className="mt-4">
            <ErrorState title="Prediction failed" message={actionError} />
          </div>
        ) : null}
        {nextHour ? (
          <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
            <div>
              <dt className="text-muted">Target hour</dt>
              <dd className="font-medium">{formatTimestamp(nextHour.forecast.utc_timestamp)}</dd>
            </div>
            <div>
              <dt className="text-muted">Predicted load</dt>
              <dd className="font-medium">{formatMw(nextHour.forecast.predicted_load_mw, 2)}</dd>
            </div>
            <div>
              <dt className="text-muted">Actual load</dt>
              <dd className="font-medium">Not yet observed</dd>
            </div>
          </dl>
        ) : null}
      </section>
    </div>
  )
}

export default Forecast

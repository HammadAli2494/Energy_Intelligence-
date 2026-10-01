import { useEffect, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import Disclaimer from '../components/common/Disclaimer'
import ErrorState from '../components/common/ErrorState'
import LoadingSpinner from '../components/common/LoadingSpinner'
import PageHeader from '../components/common/PageHeader'
import { getModelMetrics } from '../services/api'
import { formatMw, formatNumber } from '../utils/format'

const MODEL_LABELS = {
  persistence: 'Persistence',
  moving_average_24: 'Moving average 24',
  linear_regression: 'Linear regression',
  random_forest: 'Random forest',
  hist_gradient_boosting: 'Hist. gradient boosting',
}

function ModelPerformance() {
  const [payload, setPayload] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    getModelMetrics()
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
  }, [])

  const chartData = payload
    ? Object.entries(payload.metrics).map(([name, splits]) => ({
        name: MODEL_LABELS[name] || name,
        valid: splits.valid.mae,
        test: splits.test.mae,
      }))
    : []

  const selected = payload?.metrics?.[payload.selected_model]

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Evaluation"
        title="Model performance"
        description="Metrics come from the offline time-series evaluation in model_metadata.json. They are not live accuracy."
      />
      <Disclaimer>{payload?.disclaimer || 'Metrics are from the offline evaluation.'}</Disclaimer>

      {loading ? <LoadingSpinner label="Loading metrics" /> : null}
      {error ? <ErrorState title="Could not load metrics" message={error} /> : null}

      {payload ? (
        <>
          <section className="rounded-xl border border-line bg-white p-5">
            <h2 className="text-base font-semibold text-ink">Selected model</h2>
            <p className="mt-2 text-sm text-muted">
              {MODEL_LABELS[payload.selected_model] || payload.selected_model}.{' '}
              {payload.selection_rule}
            </p>
            {selected ? (
              <dl className="mt-4 grid gap-4 sm:grid-cols-2">
                <div>
                  <dt className="text-xs tracking-wide text-muted uppercase">2019 validation</dt>
                  <dd className="mt-1 text-sm">
                    MAE {formatMw(selected.valid.mae, 2)} · RMSE {formatMw(selected.valid.rmse, 2)} ·
                    MAPE {formatNumber(selected.valid.mape, 3)}%
                  </dd>
                </div>
                <div>
                  <dt className="text-xs tracking-wide text-muted uppercase">2020 test</dt>
                  <dd className="mt-1 text-sm">
                    MAE {formatMw(selected.test.mae, 2)} · RMSE {formatMw(selected.test.rmse, 2)} ·
                    MAPE {formatNumber(selected.test.mape, 3)}%
                  </dd>
                </div>
              </dl>
            ) : null}
          </section>

          <section className="rounded-xl border border-line bg-white p-5">
            <h2 className="text-base font-semibold text-ink">Validation vs test MAE</h2>
            <div className="mt-4 h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
                  <CartesianGrid stroke="#e5edf2" strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#5c6b7a' }} interval={0} />
                  <YAxis
                    tick={{ fontSize: 11, fill: '#5c6b7a' }}
                    tickFormatter={(value) => Number(value).toLocaleString('en-US')}
                    width={64}
                  />
                  <Tooltip formatter={(value) => [`${formatNumber(value, 2)} MW`, 'MAE']} />
                  <Legend />
                  <Bar dataKey="valid" name="2019 valid MAE" fill="#0f766e" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="test" name="2020 test MAE" fill="#1b2430" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="overflow-x-auto rounded-xl border border-line bg-white">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-line bg-canvas text-xs tracking-wide text-muted uppercase">
                <tr>
                  <th className="px-4 py-3 font-medium">Model</th>
                  <th className="px-4 py-3 font-medium">Valid MAE</th>
                  <th className="px-4 py-3 font-medium">Test MAE</th>
                  <th className="px-4 py-3 font-medium">Valid MAPE</th>
                  <th className="px-4 py-3 font-medium">Test MAPE</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(payload.metrics).map(([name, splits]) => (
                  <tr key={name} className="border-b border-line last:border-0">
                    <td className="px-4 py-3 font-medium">
                      {MODEL_LABELS[name] || name}
                      {name === payload.selected_model ? ' (selected)' : ''}
                    </td>
                    <td className="px-4 py-3">{formatMw(splits.valid.mae, 2)}</td>
                    <td className="px-4 py-3">{formatMw(splits.test.mae, 2)}</td>
                    <td className="px-4 py-3">{formatNumber(splits.valid.mape, 3)}%</td>
                    <td className="px-4 py-3">{formatNumber(splits.test.mape, 3)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="rounded-xl border border-line bg-white p-5">
            <h2 className="text-base font-semibold text-ink">Split and notes</h2>
            <ul className="mt-3 list-disc space-y-1 pl-5 text-sm leading-6 text-muted">
              <li>Train: {payload.split.train}</li>
              <li>Valid: {payload.split.valid}</li>
              <li>Test: {payload.split.test}</li>
              <li>Shuffled: {String(payload.split.shuffled)}</li>
              {payload.notes.map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
          </section>
        </>
      ) : null}
    </div>
  )
}

export default ModelPerformance

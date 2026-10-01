import { Link } from 'react-router-dom'
import { formatMw, formatNumber } from '../../utils/format'

function ModelPerformanceCard({ performance }) {
  if (!performance?.valid) {
    return <p className="text-sm text-muted">Model evaluation metrics are unavailable.</p>
  }

  return (
    <div className="space-y-3 text-sm">
      <p>
        <span className="font-medium text-ink">{performance.selected_model}</span>
        <span className="text-muted"> · selected by {performance.selection_rule}</span>
      </p>
      <dl className="grid gap-3 sm:grid-cols-2">
        <div>
          <dt className="text-xs tracking-wide text-muted uppercase">2019 validation</dt>
          <dd className="mt-1 text-ink">
            MAE {formatMw(performance.valid.mae, 2)}
            {performance.valid.rmse != null ? ` · RMSE ${formatMw(performance.valid.rmse, 2)}` : ''}
            {performance.valid.mape != null ? ` · MAPE ${formatNumber(performance.valid.mape, 3)}%` : ''}
          </dd>
        </div>
        <div>
          <dt className="text-xs tracking-wide text-muted uppercase">2020 test</dt>
          <dd className="mt-1 text-ink">
            MAE {formatMw(performance.test?.mae, 2)}
            {performance.test?.rmse != null ? ` · RMSE ${formatMw(performance.test.rmse, 2)}` : ''}
            {performance.test?.mape != null ? ` · MAPE ${formatNumber(performance.test.mape, 3)}%` : ''}
          </dd>
        </div>
      </dl>
      {performance.split ? (
        <p className="text-xs text-muted">
          Split: train {performance.split.train}; valid {performance.split.valid}; test{' '}
          {performance.split.test}. Rows were not shuffled.
        </p>
      ) : null}
      <Link to="/model" className="inline-block text-sm font-medium text-brand hover:text-brand-dark">
        Full evaluation table
      </Link>
    </div>
  )
}

export default ModelPerformanceCard

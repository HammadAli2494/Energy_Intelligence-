import { Link } from 'react-router-dom'
import { formatMw, formatNumber, formatTimestamp } from '../../utils/format'

function RecentForecasts({ rows, source }) {
  if (!rows?.length) {
    return <p className="text-sm text-muted">Recent forecast rows are unavailable.</p>
  }

  return (
    <div className="overflow-x-auto">
      {source === 'mongodb' ? (
        <p className="mb-2 text-xs text-muted">Loaded from MongoDB forecast_history.</p>
      ) : (
        <p className="mb-2 text-xs text-muted">
          Loaded from the modeled feature table. Persist to MongoDB after setting MONGODB_URI.
        </p>
      )}
      <table className="min-w-full text-left text-sm">
        <thead className="border-b border-line bg-canvas text-xs tracking-wide text-muted uppercase">
          <tr>
            <th className="px-3 py-2 font-medium">Time</th>
            <th className="px-3 py-2 font-medium">Actual</th>
            <th className="px-3 py-2 font-medium">Forecast</th>
            <th className="px-3 py-2 font-medium">Difference</th>
            <th className="px-3 py-2 font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.utc_timestamp} className="border-b border-line last:border-0">
              <td className="whitespace-nowrap px-3 py-2">{formatTimestamp(row.utc_timestamp)}</td>
              <td className="px-3 py-2">{formatMw(row.actual_load_mw, 0)}</td>
              <td className="px-3 py-2">{formatMw(row.predicted_load_mw, 0)}</td>
              <td className="px-3 py-2">
                {row.residual_mw == null
                  ? '—'
                  : `${row.residual_mw > 0 ? '+' : ''}${formatNumber(row.residual_mw, 1)} MW`}
              </td>
              <td className="px-3 py-2">
                {row.status === 'Anomaly' ? (
                  <Link
                    to={`/anomalies/${encodeURIComponent(row.utc_timestamp.replace(/\+00:00$/, 'Z'))}`}
                    className="font-medium text-amber-800 hover:underline"
                  >
                    Anomaly
                  </Link>
                ) : (
                  <span className="text-muted">Normal</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default RecentForecasts

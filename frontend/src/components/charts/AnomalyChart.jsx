import {
  CartesianGrid,
  Legend,
  Line,
  ResponsiveContainer,
  Scatter,
  ComposedChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { chartTime, formatMw } from '../../utils/format'

function AnomalyChart({ data }) {
  if (!data?.length) {
    return (
      <p className="py-12 text-center text-sm text-muted">
        Anomaly series is currently unavailable.
      </p>
    )
  }

  const chartData = data.map((point) => ({
    label: chartTime(point.utc_timestamp),
    residual: point.abs_residual_mw,
    flagged: point.severity ? point.abs_residual_mw : null,
  }))

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
          <CartesianGrid stroke="#e5edf2" strokeDasharray="3 3" />
          <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#5c6b7a' }} minTickGap={28} />
          <YAxis
            tick={{ fontSize: 11, fill: '#5c6b7a' }}
            tickFormatter={(value) => Number(value).toLocaleString('en-US')}
            width={56}
            label={{ value: '|Residual| (MW)', angle: -90, position: 'insideLeft', fontSize: 11, fill: '#5c6b7a' }}
          />
          <Tooltip
            formatter={(value, name) => [formatMw(value, 1), name]}
            labelFormatter={(label) => `${label} UTC`}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="residual"
            name="Absolute residual"
            stroke="#94a3b8"
            dot={false}
            strokeWidth={1.25}
          />
          <Scatter dataKey="flagged" name="Flagged hour" fill="#b45309" />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

export default AnomalyChart

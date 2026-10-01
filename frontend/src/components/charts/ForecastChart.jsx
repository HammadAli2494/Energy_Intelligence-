import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { chartTime, formatMw } from '../../utils/format'

function ForecastChart({ data }) {
  if (!data?.length) {
    return (
      <p className="py-16 text-center text-sm text-muted">
        Forecast data is currently unavailable.
      </p>
    )
  }

  const chartData = data.map((point) => ({
    ...point,
    label: chartTime(point.utc_timestamp),
  }))

  return (
    <div className="h-80 w-full sm:h-96">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 8, right: 12, left: 4, bottom: 8 }}>
          <CartesianGrid stroke="#e5edf2" strokeDasharray="3 3" />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 11, fill: '#5c6b7a' }}
            minTickGap={28}
            label={{ value: 'Date / Time (UTC)', position: 'insideBottom', offset: -2, fontSize: 11, fill: '#5c6b7a' }}
          />
          <YAxis
            tick={{ fontSize: 11, fill: '#5c6b7a' }}
            tickFormatter={(value) => Number(value).toLocaleString('en-US')}
            width={72}
            label={{ value: 'Demand (MW)', angle: -90, position: 'insideLeft', offset: 10, fontSize: 11, fill: '#5c6b7a' }}
          />
          <Tooltip
            formatter={(value, name) => [formatMw(value, 1), name]}
            labelFormatter={(label) => `${label} UTC`}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="actual_load_mw"
            name="Actual demand"
            stroke="#1b2430"
            dot={false}
            strokeWidth={1.75}
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="predicted_load_mw"
            name="Forecast demand"
            stroke="#0f766e"
            dot={false}
            strokeWidth={1.75}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default ForecastChart

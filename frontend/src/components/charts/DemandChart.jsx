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

function DemandChart({ data }) {
  const chartData = data.map((point) => ({
    ...point,
    label: chartTime(point.utc_timestamp),
  }))

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
          <CartesianGrid stroke="#e5edf2" strokeDasharray="3 3" />
          <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#5c6b7a' }} minTickGap={24} />
          <YAxis
            tick={{ fontSize: 11, fill: '#5c6b7a' }}
            tickFormatter={(value) => Number(value).toLocaleString('en-US')}
            width={64}
          />
          <Tooltip
            formatter={(value, name) => [formatMw(value, 1), name]}
            labelFormatter={(label) => `${label} UTC`}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="actual_load_mw"
            name="Actual"
            stroke="#1b2430"
            dot={false}
            strokeWidth={2}
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="predicted_load_mw"
            name="Predicted"
            stroke="#0f766e"
            dot={false}
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default DemandChart

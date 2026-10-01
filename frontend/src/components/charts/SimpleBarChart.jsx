import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { formatMw } from '../../utils/format'

function SimpleBarChart({ data, xKey, yKey, xFormatter }) {
  const chartData = data.map((row) => ({
    ...row,
    label: xFormatter ? xFormatter(row[xKey]) : row[xKey],
  }))

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
          <CartesianGrid stroke="#e5edf2" strokeDasharray="3 3" />
          <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#5c6b7a' }} />
          <YAxis
            tick={{ fontSize: 11, fill: '#5c6b7a' }}
            tickFormatter={(value) => Number(value).toLocaleString('en-US')}
            width={64}
          />
          <Tooltip formatter={(value) => [formatMw(value, 1), 'Mean demand']} />
          <Bar dataKey={yKey} fill="#0f766e" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default SimpleBarChart

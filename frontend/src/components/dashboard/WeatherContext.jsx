import { formatNumber } from '../../utils/format'

function WeatherContext({ weather }) {
  if (!weather) {
    return <p className="text-sm text-muted">Weather context is unavailable.</p>
  }

  const cells = [
    { label: 'Temperature', value: weather.temperature_c, suffix: '°C', digits: 1 },
    { label: 'Humidity', value: weather.relative_humidity_pct, suffix: '%', digits: 0 },
    { label: 'Wind speed', value: weather.wind_speed_kmh, suffix: 'km/h', digits: 1 },
  ]

  return (
    <div>
      <p className="text-xs text-muted">
        {weather.location_name || 'Madrid'}
        {weather.latitude != null && weather.longitude != null
          ? ` · ${weather.latitude}, ${weather.longitude}`
          : ''}
      </p>
      <p className="mt-1 text-xs text-muted">{weather.timing}</p>
      <dl className="mt-3 grid grid-cols-3 gap-3 text-sm">
        {cells.map((cell) => (
          <div key={cell.label}>
            <dt className="text-muted">{cell.label}</dt>
            <dd className="mt-0.5 font-medium text-ink">
              {cell.value == null ? '—' : `${formatNumber(cell.value, cell.digits)} ${cell.suffix}`}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  )
}

export default WeatherContext

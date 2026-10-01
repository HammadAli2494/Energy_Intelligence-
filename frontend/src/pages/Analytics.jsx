import { useEffect, useState } from 'react'
import SimpleBarChart from '../components/charts/SimpleBarChart'
import Disclaimer from '../components/common/Disclaimer'
import ErrorState from '../components/common/ErrorState'
import LoadingSpinner from '../components/common/LoadingSpinner'
import PageHeader from '../components/common/PageHeader'
import { getAnalytics } from '../services/api'
import { monthLabel, weekdayLabel } from '../utils/format'

function Analytics() {
  const [payload, setPayload] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    getAnalytics()
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

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Patterns"
        title="Analytics"
        description="Average demand by hour, weekday, month, and Madrid temperature bin from the modeled feature table."
      />
      <Disclaimer>
        These averages describe the historical feature table. They are not live grid
        telemetry.
      </Disclaimer>

      {loading ? <LoadingSpinner label="Loading analytics" /> : null}
      {error ? <ErrorState title="Could not load analytics" message={error} /> : null}

      {payload ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <section className="rounded-xl border border-line bg-white p-5">
            <h2 className="text-base font-semibold text-ink">Mean load by local hour</h2>
            <SimpleBarChart data={payload.hourly} xKey="hour" yKey="mean_load_mw" />
          </section>
          <section className="rounded-xl border border-line bg-white p-5">
            <h2 className="text-base font-semibold text-ink">Mean load by weekday</h2>
            <SimpleBarChart
              data={payload.weekly}
              xKey="day_of_week"
              yKey="mean_load_mw"
              xFormatter={weekdayLabel}
            />
          </section>
          <section className="rounded-xl border border-line bg-white p-5">
            <h2 className="text-base font-semibold text-ink">Mean load by month</h2>
            <SimpleBarChart
              data={payload.monthly}
              xKey="month"
              yKey="mean_load_mw"
              xFormatter={monthLabel}
            />
          </section>
          <section className="rounded-xl border border-line bg-white p-5">
            <h2 className="text-base font-semibold text-ink">Mean load by temperature</h2>
            <SimpleBarChart
              data={payload.temperature_bins}
              xKey="temperature_c"
              yKey="mean_load_mw"
              xFormatter={(value) => `${value}°C`}
            />
          </section>
        </div>
      ) : null}
    </div>
  )
}

export default Analytics

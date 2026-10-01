import PageHeader from '../components/common/PageHeader'

const architectureSteps = [
  { title: 'Historical energy data', body: 'Spain hourly ENTSO-E load from Open Power System Data (through September 2020).' },
  { title: 'Open-Meteo weather', body: 'Madrid temperature, humidity, and wind speed. Last-known hour (t−1) is the model input.' },
  { title: 'Feature engineering', body: 'Calendar, lags, and rolling means that never include load at the target hour.' },
  { title: 'Forecasting model', body: 'Offline Histogram Gradient Boosting, loaded by FastAPI at startup.' },
  { title: 'Anomaly detection', body: 'Residual screen against 2× / 3× 2019 validation MAE.' },
  { title: 'React + MongoDB', body: 'Dashboard reads the API. MongoDB stores contact messages and, when configured, forecast and anomaly history.' },
]

function Methodology() {
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="About"
        title="Methodology and architecture"
        description="How the data, model, and application are put together. The Dashboard shows results; this page explains the pipeline."
      />

      <section className="rounded-lg border border-line bg-white p-5">
        <h2 className="text-base font-semibold text-ink">What this project does</h2>
        <p className="mt-2 text-sm leading-6 text-muted">
          Energy Intelligence estimates Spain’s next-hour national electricity demand and
          flags hours where actual load differs unusually from that forecast. Training is
          offline. The API loads the saved model. Charts use the last hours in the OPSD
          extract, not a live grid feed.
        </p>
      </section>

      <section className="rounded-lg border border-line bg-white p-5">
        <h2 className="text-base font-semibold text-ink">System architecture</h2>
        <ol className="mt-4 grid gap-3 sm:grid-cols-2">
          {architectureSteps.map((step, index) => (
            <li key={step.title} className="rounded-lg border border-line px-4 py-3">
              <p className="text-xs font-medium text-brand">
                {index + 1}. {step.title}
              </p>
              <p className="mt-1 text-sm leading-6 text-muted">{step.body}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="rounded-lg border border-line bg-white p-5">
        <h2 className="text-base font-semibold text-ink">Data sources</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-6 text-muted">
          <li>Open Power System Data time series 2020-10-06 — Spain ENTSO-E Transparency load.</li>
          <li>Open-Meteo — Madrid hourly weather (no API key). Coordinates live in backend/.env.</li>
          <li>MongoDB Atlas — optional persistence for forecasts, anomalies, model-run metadata, and contact messages.</li>
        </ul>
      </section>

      <section className="rounded-lg border border-line bg-white p-5">
        <h2 className="text-base font-semibold text-ink">Data preparation and features</h2>
        <p className="mt-2 text-sm leading-6 text-muted">
          Short interior gaps in load are interpolated. Longer gaps stay missing. Each
          feature row is hour <em>t</em>. Lags and rolling means end at t−1. Weather is
          the last known Madrid hour, not observed weather at t.
        </p>
      </section>

      <section className="rounded-lg border border-line bg-white p-5">
        <h2 className="text-base font-semibold text-ink">Leakage controls</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-6 text-muted">
          <li>Rows are never shuffled. Train is before 2019, validation is 2019, test is 2020.</li>
          <li>The target load at t is not an input.</li>
          <li>The official ENTSO-E load forecast is not used as a feature.</li>
        </ul>
      </section>

      <section className="rounded-lg border border-line bg-white p-5">
        <h2 className="text-base font-semibold text-ink">Forecasting model</h2>
        <p className="mt-2 text-sm leading-6 text-muted">
          Persistence, a 24-hour moving average, linear regression, random forest, and
          histogram gradient boosting were compared on 2019 validation MAE. Histogram
          gradient boosting was selected (227.02 MW). 2020 test MAE is 311.33 MW; that
          year includes COVID-related demand changes and was not used to pick the model.
          FastAPI serves the saved joblib file. React does not retrain the model.
        </p>
      </section>

      <section className="rounded-lg border border-line bg-white p-5">
        <h2 className="text-base font-semibold text-ink">Anomaly detection</h2>
        <p className="mt-2 text-sm leading-6 text-muted">
          An hour is flagged if |actual − predicted| is at least twice (medium) or three
          times (high) the 2019 validation MAE. That is a residual screen, not a claim of
          equipment or grid failure.
        </p>
      </section>

      <section className="rounded-lg border border-line bg-white p-5">
        <h2 className="text-base font-semibold text-ink">Limitations</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-6 text-muted">
          <li>The published extract ends on 30 September 2020.</li>
          <li>National load is paired with a single Madrid weather point.</li>
          <li>Forecasts are estimates for a portfolio project, not operational decisions.</li>
        </ul>
      </section>
    </div>
  )
}

export default Methodology

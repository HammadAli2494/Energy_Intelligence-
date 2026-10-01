import PageHeader from '../components/common/PageHeader'

function Terms() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Legal"
        title="Terms of use"
        description="Use this project as an educational demonstration."
      />
      <section className="space-y-3 rounded-xl border border-line bg-white p-5 text-sm leading-6 text-muted">
        <p>
          Forecasts, residuals, and anomaly flags are estimates from a model trained on
          historical data through September 2020. They are not advice for generation
          scheduling, trading, or emergency response.
        </p>
        <p>
          The software is provided as-is under the MIT license. Dataset licenses remain
          with Open Power System Data, ENTSO-E Transparency, and Open-Meteo.
        </p>
        <p>
          Do not treat a residual spike as evidence that equipment failed. Do not rely
          on this UI as a live grid monitor.
        </p>
      </section>
    </div>
  )
}

export default Terms

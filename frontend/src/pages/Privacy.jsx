import PageHeader from '../components/common/PageHeader'

function Privacy() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Legal"
        title="Privacy"
        description="This is a student portfolio application, not a commercial product."
      />
      <section className="space-y-3 rounded-xl border border-line bg-white p-5 text-sm leading-6 text-muted">
        <p>
          The dashboard shows public historical electricity load from Open Power System
          Data and weather from Open-Meteo. Those datasets are not personal data.
        </p>
        <p>
          If you use the contact form and MongoDB is configured, the API stores your
          name, email, subject, and message so the project owner can read them. Fields
          are length-limited. There is no advertising tracker and no account system.
        </p>
        <p>
          If MongoDB is not configured, the contact endpoint refuses the request and
          nothing is stored.
        </p>
        <p>
          Frontend environment variables are public. Secrets belong only in the backend
          <code className="mx-1">.env</code> file, which is not committed.
        </p>
      </section>
    </div>
  )
}

export default Privacy

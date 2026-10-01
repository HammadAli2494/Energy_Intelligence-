import { Link } from 'react-router-dom'

function NotFound() {
  return (
    <section className="rounded-2xl border border-line bg-white px-6 py-12 text-center">
      <h1 className="text-2xl font-semibold text-ink">Page not found</h1>
      <p className="mt-2 text-sm text-muted">That route is not part of this application.</p>
      <Link
        to="/"
        className="mt-6 inline-block rounded-md bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark"
      >
        Back to home
      </Link>
    </section>
  )
}

export default NotFound

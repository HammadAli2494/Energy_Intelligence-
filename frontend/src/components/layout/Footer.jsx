import { Link } from 'react-router-dom'

function Footer() {
  return (
    <footer className="border-t border-line bg-white">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-5 text-sm text-muted sm:px-6 lg:px-8">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <p>Energy Intelligence — educational portfolio project.</p>
          <p>Forecasts are estimates, not operational dispatch instructions.</p>
        </div>
        <nav className="flex flex-wrap gap-x-4 gap-y-2" aria-label="Legal">
          <Link to="/about" className="hover:text-ink">
            About
          </Link>
          <Link to="/contact" className="hover:text-ink">
            Contact
          </Link>
          <Link to="/privacy" className="hover:text-ink">
            Privacy
          </Link>
          <Link to="/terms" className="hover:text-ink">
            Terms
          </Link>
        </nav>
      </div>
    </footer>
  )
}

export default Footer

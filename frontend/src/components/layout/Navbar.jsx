import { useState } from 'react'
import { Link, NavLink } from 'react-router-dom'

const links = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/forecast', label: 'Forecast' },
  { to: '/anomalies', label: 'Anomalies' },
  { to: '/analytics', label: 'Analytics' },
  { to: '/model', label: 'Model' },
  { to: '/about', label: 'About' },
]

function linkClass(isActive) {
  return `text-sm font-medium ${isActive ? 'text-brand-dark' : 'text-muted hover:text-ink'}`
}

function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <header className="border-b border-line bg-white">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-3 no-underline">
          <span className="flex h-8 w-8 items-center justify-center rounded bg-brand text-xs font-semibold text-white">
            EI
          </span>
          <span>
            <span className="block text-sm font-semibold text-ink">Energy Intelligence</span>
            <span className="block text-xs text-muted">Demand forecasting</span>
          </span>
        </Link>

        <nav className="hidden items-center gap-5 lg:flex" aria-label="Primary">
          {links.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => linkClass(isActive)}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <button
          type="button"
          className="rounded border border-line px-3 py-1.5 text-sm text-ink lg:hidden"
          aria-expanded={menuOpen}
          aria-controls="mobile-nav"
          onClick={() => setMenuOpen((open) => !open)}
        >
          {menuOpen ? 'Close' : 'Menu'}
        </button>
      </div>

      {menuOpen ? (
        <nav
          id="mobile-nav"
          className="border-t border-line px-4 py-3 lg:hidden"
          aria-label="Mobile"
        >
          {links.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className="block py-2 text-sm font-medium text-ink"
              onClick={() => setMenuOpen(false)}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      ) : null}
    </header>
  )
}

export default Navbar

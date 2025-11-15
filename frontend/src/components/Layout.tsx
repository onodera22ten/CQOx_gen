import { Outlet, Link, useLocation } from 'react-router-dom'
import './Layout.css'

export default function Layout() {
  const location = useLocation()

  const navItems = [
    { path: '/console', label: 'Decision Console' },
    { path: '/policy', label: 'Policy Lab' },
    { path: '/causal', label: 'Causal Design' },
    { path: '/portfolio', label: 'Portfolio & ROI' },
    { path: '/diagnostics', label: 'Diagnostics' },
  ]

  return (
    <div className="layout">
      <nav className="sidebar">
        <div className="logo">
          <h1>CQOx</h1>
          <p>Causal Query Optimizer</p>
        </div>
        <ul className="nav-list">
          {navItems.map((item) => (
            <li key={item.path}>
              <Link
                to={item.path}
                className={location.pathname === item.path ? 'active' : ''}
              >
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}

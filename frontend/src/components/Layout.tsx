import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import './Layout.css'

export default function Layout() {
  const location = useLocation()
  const { user, logout } = useAuth()

  const navItems = [
    { path: '/datasets', label: '📁 データ管理', permission: null, role: null },
    { path: '/causal', label: '  └─ Causal Design', permission: 'models:read', role: null },
    { path: '/console', label: 'Decision Console', permission: null, role: null },
    { path: '/decision-console-v1', label: '[v1] マーケ施策判定', permission: null, role: null },
    { path: '/policy', label: 'Policy Lab', permission: 'models:write', role: null },
    { path: '/diagnostics', label: 'Diagnostics', permission: 'diagnostics:read', role: null },
    { path: '/visualizations', label: '📊 Visualizations', permission: 'models:read', role: null },
    { path: '/portfolio', label: 'Portfolio & ROI', permission: 'policies:read', role: null },
    { path: '/digital-twin', label: '👥 Digital Twin', permission: 'models:read', role: null },
    { path: '/export-gate', label: '📤 Export Gate', permission: 'policies:read', role: null },
    { path: '/admin', label: 'Admin Panel', permission: null, role: 'admin' },
  ]

  // Filter nav items based on user permissions/roles
  const visibleNavItems = navItems.filter(item => {
    if (item.role && user && !user.roles.includes(item.role)) {
      return false;
    }
    return true;
  })

  const handleLogout = async () => {
    await logout()
  }

  // Get user role badge color
  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-red-100 text-red-800'
      case 'analyst':
        return 'bg-blue-100 text-blue-800'
      case 'viewer':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="layout">
      <nav className="sidebar">
        <div className="logo">
          <h1>CQOx</h1>
          <p>Causal Query Optimizer</p>
        </div>

        {/* User info */}
        {user && (
          <div className="user-info" style={{
            padding: '1rem',
            borderBottom: '1px solid #e5e7eb',
            marginBottom: '1rem'
          }}>
            <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>
              Signed in as
            </div>
            <div style={{ fontWeight: '600', marginBottom: '0.5rem' }}>
              {user.email}
            </div>
            <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
              {user.roles.map((role) => (
                <span
                  key={role}
                  className={getRoleBadgeColor(role)}
                  style={{
                    fontSize: '0.75rem',
                    padding: '0.125rem 0.5rem',
                    borderRadius: '9999px',
                    fontWeight: '500'
                  }}
                >
                  {role}
                </span>
              ))}
            </div>
          </div>
        )}

        <ul className="nav-list">
          {visibleNavItems.map((item) => (
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

        {/* Logout button */}
        <div style={{ marginTop: 'auto', padding: '1rem', borderTop: '1px solid #e5e7eb' }}>
          <button
            onClick={handleLogout}
            style={{
              width: '100%',
              padding: '0.5rem 1rem',
              backgroundColor: '#ef4444',
              color: 'white',
              border: 'none',
              borderRadius: '0.375rem',
              fontSize: '0.875rem',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'background-color 0.2s'
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#dc2626'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#ef4444'}
          >
            Logout
          </button>
        </div>
      </nav>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}

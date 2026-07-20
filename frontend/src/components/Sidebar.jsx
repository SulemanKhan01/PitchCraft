import { NavLink, useNavigate } from 'react-router-dom'
import { useState, useCallback } from 'react'
import { useClerk, useUser } from '@clerk/clerk-react'
// import useAuthStore from '../stores/useAuthStore'  // JWT — replaced by Clerk
import './Sidebar.css'

function Sidebar({ onCollapse }) {
  const [collapsed, setCollapsed] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)

  // const logout = useAuthStore((s) => s.logout)  // JWT — replaced by Clerk
  // const user = useAuthStore((s) => s.user)       // JWT — replaced by Clerk
  const { signOut } = useClerk()
  const { user } = useUser()
  const navigate = useNavigate()

  /* Get the first two letters of the email for the avatar */
  const userEmail = user?.primaryEmailAddress?.emailAddress || 'user@example.com'
  const initials = userEmail.slice(0, 2).toUpperCase()

  function handleLogout() {
    signOut()
    navigate('/login')
  }

  const toggleSidebar = useCallback(() => {
    setCollapsed(prev => {
      const next = !prev
      if (onCollapse) onCollapse(next)
      return next
    })
  }, [onCollapse])

  return (
    <aside className={`sidebar${collapsed ? ' sidebar--collapsed' : ''}`}>
      <div className="sidebar__glass" />

      {/* Header */}
      <div className="sidebar__header">
        <div className="sidebar__logo">
          <div className="sidebar__logo-icon-wrap">
            <svg className="sidebar__logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>
          {!collapsed && (
            <span className="sidebar__logo-text">
              Pitch<span className="sidebar__logo-accent">Craft</span>
            </span>
          )}
        </div>

        <button
          className="sidebar__toggle"
          onClick={toggleSidebar}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          type="button"
        >
          <svg className="sidebar__toggle-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            {collapsed ? (
              <path d="M9 18l6-6-6-6" />
            ) : (
              <path d="M15 18l-6-6 6-6" />
            )}
          </svg>
        </button>
      </div>

      {/* Navigation */}
      <nav className="sidebar__nav">

        {/* Main Nav */}
        <div className="sidebar__section">
          <NavLink to="/chat" className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}>
            <span className="sidebar__link-icon-wrap">
              <svg className="sidebar__link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
              </svg>
            </span>
            {!collapsed && <span className="sidebar__link-text">Chat</span>}
          </NavLink>

          <NavLink to="/upload" className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}>
            <span className="sidebar__link-icon-wrap">
              <svg className="sidebar__link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                <polyline points="14,2 14,8 20,8" />
                <line x1="12" y1="18" x2="12" y2="12" />
                <polyline points="9,15 12,12 15,15" />
              </svg>
            </span>
            {!collapsed && <span className="sidebar__link-text">Upload Proposals</span>}
          </NavLink>

          <NavLink to="/cover-letter" className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}>
            <span className="sidebar__link-icon-wrap">
              <svg className="sidebar__link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                <polyline points="22,6 12,13 2,6" />
              </svg>
            </span>
            {!collapsed && <span className="sidebar__link-text">Cover Letter</span>}
          </NavLink>
        </div>

        {/* AI Tools Section */}
        {!collapsed && <div className="sidebar__section-label">AI TOOLS</div>}
        <div className="sidebar__section">
          <button className="sidebar__link sidebar__link-btn">
            <span className="sidebar__link-icon-wrap">
              <svg className="sidebar__link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="7" height="7" rx="1" />
                <rect x="14" y="3" width="7" height="7" rx="1" />
                <rect x="3" y="14" width="7" height="7" rx="1" />
                <rect x="14" y="14" width="7" height="7" rx="1" />
              </svg>
            </span>
            {!collapsed && <span className="sidebar__link-text">Templates</span>}
          </button>

          <button className="sidebar__link sidebar__link-btn">
            <span className="sidebar__link-icon-wrap">
              <svg className="sidebar__link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z" />
              </svg>
            </span>
            {!collapsed && <span className="sidebar__link-text">My Documents</span>}
          </button>

          <button className="sidebar__link sidebar__link-btn">
            <span className="sidebar__link-icon-wrap">
              <svg className="sidebar__link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="3" />
                <path d="M19.07 4.93a10 10 0 010 14.14M4.93 4.93a10 10 0 000 14.14" />
              </svg>
            </span>
            {!collapsed && <span className="sidebar__link-text">Settings</span>}
          </button>
        </div>

        {/* Account Section */}
        {!collapsed && <div className="sidebar__section-label">ACCOUNT</div>}
        <div className="sidebar__section">
          <button className="sidebar__link sidebar__link-btn">
            <span className="sidebar__link-icon-wrap">
              <svg className="sidebar__link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
            </span>
            {!collapsed && <span className="sidebar__link-text">Profile</span>}
          </button>

          <button className="sidebar__link sidebar__link-btn">
            <span className="sidebar__link-icon-wrap">
              <svg className="sidebar__link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <rect x="1" y="4" width="22" height="16" rx="2" ry="2" />
                <line x1="1" y1="10" x2="23" y2="10" />
              </svg>
            </span>
            {!collapsed && <span className="sidebar__link-text">Billing</span>}
          </button>

          <button className="sidebar__link sidebar__link-btn sidebar__link-logout" onClick={handleLogout} type="button">
            <span className="sidebar__link-icon-wrap">
              <svg className="sidebar__link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
            </span>
            {!collapsed && <span className="sidebar__link-text">Log out</span>}
          </button>
        </div>
      </nav>

      {/* Gemini Banner */}
      {!collapsed && (
        <div className="sidebar__gemini-banner">
          <div className="sidebar__gemini-info">
            <div className="sidebar__gemini-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
              </svg>
            </div>
            <div>
              <div className="sidebar__gemini-title">Built with Gemini AI</div>
              <div className="sidebar__gemini-sub">Smart. Fast. Accurate.</div>
            </div>
          </div>
          <button className="sidebar__gemini-btn" type="button">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      )}

      {/* User Profile Footer */}
      <div className="sidebar__user-footer">
        <div className="sidebar__user-avatar">{initials}</div>
        {!collapsed && (
          <div className="sidebar__user-info">
            <div className="sidebar__user-name">{userEmail.split('@')[0]}</div>
            <div className="sidebar__user-email">{userEmail}</div>
          </div>
        )}
        {!collapsed && (
          <button className="sidebar__user-menu-btn" type="button" onClick={handleLogout} title="Log out">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
          </button>
        )}
      </div>
    </aside>
  )
}

export default Sidebar
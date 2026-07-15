/* ============================================
   Sidebar Component
   ============================================

   CONCEPT: A React component is a function that returns JSX.

   - "import" brings in tools from other files
   - "export default" makes this component available to other files
   - "NavLink" is like <a> but prevents full page reloads (SPA navigation)
   - "to" prop tells NavLink which URL to navigate to
   - "className" is a function — when the link's URL matches, it returns "active"
     so react-router-dom automatically highlights the current page

   PROPS we accept:
   - None needed! The Sidebar is self-contained.
     It uses react-router-dom's NavLink which knows the current URL automatically.
   ============================================ */

import { NavLink } from 'react-router-dom'
import './Sidebar.css'

function Sidebar() {
  return (
    <aside className="sidebar">
      {/* HEADER — Logo */}
      <div className="sidebar-header">
        <div className="sidebar-logo">
          Pitch<span>Craft</span>
        </div>
      </div>

      {/* NAVIGATION — Links to each page */}
      <nav className="sidebar-nav">
        {/* NavLink is like <a> but:
            1. Prevents full page reload (stays in the SPA)
            2. Adds "active" class automatically when URL matches */}
        <NavLink
          to="/chat"
          className={({ isActive }) =>
            `sidebar-link${isActive ? ' active' : ''}`
          }
        >
          <span className="sidebar-link-icon">💬</span>
          Chat
        </NavLink>

        <NavLink
          to="/upload"
          className={({ isActive }) =>
            `sidebar-link${isActive ? ' active' : ''}`
          }
        >
          <span className="sidebar-link-icon">📄</span>
          Upload Proposals
        </NavLink>

        <NavLink
          to="/cover-letter"
          className={({ isActive }) =>
            `sidebar-link${isActive ? ' active' : ''}`
          }
        >
          <span className="sidebar-link-icon">✉️</span>
          Cover Letter
        </NavLink>
      </nav>

      {/* FOOTER */}
      <div className="sidebar-footer">
        Built with Gemini AI
      </div>
    </aside>
  )
}

export default Sidebar

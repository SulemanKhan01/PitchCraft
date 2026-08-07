import { NavLink, useNavigate, useSearchParams } from 'react-router-dom'
import { useState, useCallback, useEffect } from 'react'
import { useClerk, useUser, useAuth } from '@clerk/clerk-react'
import { listConversations, createConversation, deleteConversation } from '../services/api'
import './Sidebar.css'

function Sidebar({ onCollapse }) {
  const [collapsed, setCollapsed] = useState(false)
  const [conversations, setConversations] = useState([])
  const [loadingConvs, setLoadingConvs] = useState(false)

  const { signOut } = useClerk()
  const { user } = useUser()
  const { getToken } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const activeConvId = searchParams.get('id')

  const userEmail = user?.primaryEmailAddress?.emailAddress || 'user@example.com'
  const initials = userEmail.slice(0, 2).toUpperCase()

  // ── Fetch Conversations List ──────────────────────────────────────────────
  const loadConversations = useCallback(async () => {
    try {
      setLoadingConvs(true)
      const token = await getToken()
      const list = await listConversations(token)
      setConversations(list || [])
    } catch (err) {
      console.error('Failed to load conversations:', err)
    } finally {
      setLoadingConvs(false)
    }
  }, [getToken])

  useEffect(() => {
    loadConversations()
  }, [loadConversations, activeConvId])

  // ── Handlers ──────────────────────────────────────────────────────────────
  async function handleNewChat() {
    try {
      const token = await getToken()
      const newConv = await createConversation(token)
      await loadConversations()
      navigate(`/chat?id=${newConv.id}`)
    } catch (err) {
      console.error('Failed to create conversation:', err)
    }
  }

  async function handleDeleteChat(e, convId) {
    e.stopPropagation()
    e.preventDefault()
    try {
      const token = await getToken()
      await deleteConversation(convId, token)
      await loadConversations()
      if (activeConvId === convId) {
        navigate('/chat')
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err)
    }
  }

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
            {collapsed ? <path d="M9 18l6-6-6-6" /> : <path d="M15 18l-6-6 6-6" />}
          </svg>
        </button>
      </div>

      {/* Navigation */}
      <nav className="sidebar__nav">

        {/* New Chat Button */}
        <button className="sidebar__new-chat-btn" onClick={handleNewChat} type="button">
          <span className="sidebar__link-icon-wrap">
            <svg className="sidebar__link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
          </span>
          {!collapsed && <span>New Chat</span>}
        </button>

        {/* Main Nav */}
        <div className="sidebar__section">
          <NavLink to="/chat" className={({ isActive }) => `sidebar__link${isActive && !activeConvId ? ' sidebar__link--active' : ''}`}>
            <span className="sidebar__link-icon-wrap">
              <svg className="sidebar__link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
              </svg>
            </span>
            {!collapsed && <span className="sidebar__link-text">Chat Home</span>}
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

        {/* Recent Chats Section */}
        {!collapsed && <div className="sidebar__section-label">RECENT CHATS</div>}
        <div className="sidebar__section sidebar__recent-list">
          {conversations.map(conv => (
            <div
              key={conv.id}
              className={`sidebar__link sidebar__recent-item${activeConvId === conv.id ? ' sidebar__link--active' : ''}`}
              onClick={() => navigate(`/chat?id=${conv.id}`)}
            >
              <span className="sidebar__link-icon-wrap">
                <svg className="sidebar__link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
                </svg>
              </span>
              {!collapsed && (
                <>
                  <span className="sidebar__link-text" title={conv.title}>
                    {conv.title || 'New Conversation'}
                  </span>
                  <button
                    className="sidebar__recent-delete"
                    onClick={(e) => handleDeleteChat(e, conv.id)}
                    title="Delete Chat"
                    type="button"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="3 6 5 6 21 6" />
                      <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
                    </svg>
                  </button>
                </>
              )}
            </div>
          ))}
        </div>

        {/* AI Tools Section */}
        {!collapsed && <div className="sidebar__section-label">SETTINGS & ACCOUNT</div>}
        <div className="sidebar__section">
          <NavLink to="/settings" className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}>
            <span className="sidebar__link-icon-wrap">
              <svg className="sidebar__link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="3" />
                <path d="M19.07 4.93a10 10 0 010 14.14M4.93 4.93a10 10 0 000 14.14" />
              </svg>
            </span>
            {!collapsed && <span className="sidebar__link-text">Settings</span>}
          </NavLink>

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
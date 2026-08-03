import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import { useState, useCallback, useEffect } from 'react'
import useSettingsStore from '../stores/useSettingsStore'

function Layout() {
  const [collapsed, setCollapsed] = useState(false)
  const theme = useSettingsStore((s) => s.theme)

  useEffect(() => {
    const root = document.documentElement
    if (theme === 'system') {
      const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      root.setAttribute('data-theme', systemDark ? 'dark' : 'light')
      root.classList.toggle('dark', systemDark)
    } else {
      root.setAttribute('data-theme', theme)
      root.classList.toggle('dark', theme === 'dark')
    }
  }, [theme])

  const handleToggle = useCallback((val) => {
    setCollapsed(val)
  }, [])

  return (
    <div style={{ display: 'flex', minHeight: '100vh', width: '100%' }}>
      {/* Sidebar */}
      <Sidebar onCollapse={handleToggle} />

      {/* Main content — shifts right to make room for sidebar */}
      <main
        className="main-content"
        style={{
          paddingLeft: collapsed ? '68px' : '240px',
          flex: 1,
          minWidth: 0,
        }}
      >
        <Outlet />
      </main>
    </div>
  )
}

export default Layout


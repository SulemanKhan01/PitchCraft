import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import { useState, useCallback } from 'react'

function Layout() {
  const [collapsed, setCollapsed] = useState(false)

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

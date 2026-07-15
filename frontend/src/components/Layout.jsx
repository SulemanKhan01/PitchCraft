/* ============================================
   Layout Component
   ============================================

   CONCEPT: Component Composition

   This component creates the app shell:
   - Sidebar (always visible on the left)
   - Main content area (changes based on URL)

   <Outlet /> is a react-router-dom placeholder.
   Think of it like a "hole" in this component where
   the matched child route's component gets rendered.

   URL: /chat      →  <Layout> renders <ChatPage /> inside <Outlet />
   URL: /upload    →  <Layout> renders <UploadPage /> inside <Outlet />
   URL: /cover-letter → <Layout> renders <CoverLetterPage /> inside <Outlet />
   ============================================ */

import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

function Layout() {
  return (
    <>
      {/* Sidebar — fixed on the left side, always visible */}
      <Sidebar />

      {/* Main content — shifts right to make room for sidebar */}
      {/* <Outlet /> is WHERE child route components appear */}
      <main className="main-content">
        <Outlet />
      </main>
    </>
  )
}

export default Layout

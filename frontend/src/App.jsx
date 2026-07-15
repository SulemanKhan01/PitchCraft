/* ============================================
   App.jsx — Root Component & Router Setup
   ============================================

   CONCEPT: React Router

   BrowserRouter: Listens to browser URL changes
   Routes:       Container for all Route definitions
   Route:        Maps a URL path to a component
   Navigate:     Programmatically redirect to another URL

   STRUCTURE:
   <BrowserRouter>
     <Routes>
       <Route element={<Layout />}>           ← Wraps child routes with sidebar
         <Route path="/chat" element={<ChatPage />} />
         <Route path="/upload" element={<UploadPage />} />
         <Route path="/cover-letter" element={<CoverLetterPage />} />
         <Route path="/" element={<Navigate to="/chat" />} />  ← Default redirect
       </Route>
     </Routes>
   </BrowserRouter>

   When URL is "/chat":
   → BrowserRouter detects URL change
   → Routes finds matching Route
   → Renders <Layout> (sidebar + <Outlet>)
   → <Outlet> renders <ChatPage />
   ============================================ */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import ChatPage from './pages/ChatPage'
import UploadPage from './pages/UploadPage'
import CoverLetterPage from './pages/CoverLetterPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Layout route — wraps children with sidebar + main content area */}
        <Route element={<Layout />}>
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/cover-letter" element={<CoverLetterPage />} />

          {/* "/" redirects to "/chat" — Navigate is like a programmatic <a> */}
          <Route path="/" element={<Navigate to="/chat" replace />} />

          {/* 404 — any unmatched URL redirects to chat */}
          <Route path="*" element={<Navigate to="/chat" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App

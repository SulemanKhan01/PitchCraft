import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import ChatPage from './pages/ChatPage'
import UploadPage from './pages/UploadPage'
import CoverLetterPage from './pages/CoverLetterPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* ── Public routes — no login needed ── */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* ── Protected routes — login required ── */}
        <Route element={<Layout />}>
          <Route path="/chat" element={
            <ProtectedRoute><ChatPage /></ProtectedRoute>
          } />
          <Route path="/upload" element={
            <ProtectedRoute><UploadPage /></ProtectedRoute>
          } />
          <Route path="/cover-letter" element={
            <ProtectedRoute><CoverLetterPage /></ProtectedRoute>
          } />
          <Route path="/" element={<Navigate to="/chat" replace />} />
          <Route path="*" element={<Navigate to="/chat" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App

// ── OLD JWT-based LoginPage (commented out) ──────────────────────────
// import { useState } from 'react'
// import { useNavigate, Link } from 'react-router-dom'
// import { loginUser } from '../services/api'
// import useAuthStore from '../stores/useAuthStore'
// import './AuthPages.css'
//
// function LoginPage() {
//   const [email, setEmail] = useState('')
//   const [password, setPassword] = useState('')
//   const [error, setError] = useState('')
//   const [loading, setLoading] = useState(false)
//   const setAuth = useAuthStore((s) => s.setAuth)
//   const navigate = useNavigate()
//   async function handleSubmit(e) {
//     e.preventDefault()
//     setError('')
//     setLoading(true)
//     try {
//       const data = await loginUser(email, password)
//       setAuth(data.access_token, { email: data.email })
//       navigate('/chat')
//     } catch (err) {
//       setError(err.message)
//     } finally {
//       setLoading(false)
//     }
//   }
//   return ( ... )
// }
// ─────────────────────────────────────────────────────────────────────

import { SignIn } from '@clerk/clerk-react'

function LoginPage() {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      backgroundColor: '#0f0f0f'
    }}>
      <SignIn routing="hash" fallbackRedirectUrl="/chat" />
    </div>
  )
}

export default LoginPage

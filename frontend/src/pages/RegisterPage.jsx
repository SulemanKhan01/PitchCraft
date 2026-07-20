// ── OLD JWT-based RegisterPage (commented out) ───────────────────────
// import { useState } from 'react'
// import { useNavigate, Link } from 'react-router-dom'
// import { registerUser } from '../services/api'
// import './AuthPages.css'
//
// function RegisterPage() {
//   const [email, setEmail] = useState('')
//   const [password, setPassword] = useState('')
//   const [error, setError] = useState('')
//   const [loading, setLoading] = useState(false)
//   const navigate = useNavigate()
//   async function handleSubmit(e) {
//     e.preventDefault()
//     try {
//       await registerUser(email, password)
//       navigate('/login')
//     } catch (err) {
//       setError(err.message)
//     }
//   }
//   return ( ... )
// }
// ─────────────────────────────────────────────────────────────────────

import { SignUp } from '@clerk/clerk-react'

function RegisterPage() {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      backgroundColor: '#0f0f0f'
    }}>
      <SignUp routing="hash" fallbackRedirectUrl="/chat" />
    </div>
  )
}

export default RegisterPage

import { Navigate } from 'react-router-dom'
import useAuthStore from '../stores/useAuthStore'

/* If the user has no token → redirect to /login
   If they do have a token → render the page normally */
function ProtectedRoute({ children }) {
  const token = useAuthStore((s) => s.token)

  if (!token) {
    return <Navigate to="/login" replace />
  }

  return children
}

export default ProtectedRoute

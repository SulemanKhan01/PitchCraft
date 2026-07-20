
// JWT AUTH***********************************

// import { Navigate } from 'react-router-dom'
// import useAuthStore from '../stores/useAuthStore'

// /* If the user has no token → redirect to /login
//    If they do have a token → render the page normally */
// function ProtectedRoute({ children }) {
//   const token = useAuthStore((s) => s.token)

//   if (!token) {
//     return <Navigate to="/login" replace />
//   }

//   return children
// }

// export default ProtectedRoute


import { useAuth } from '@clerk/clerk-react'
import { Navigate } from 'react-router-dom'
/* If the user is NOT signed in → redirect to /login
   If they ARE signed in → render the page normally */
function ProtectedRoute({ children }) {
  const { isSignedIn, isLoaded } = useAuth()
  // Wait for Clerk to finish loading before deciding
  if (!isLoaded) {
    return <div>Loading...</div>
  }
  if (!isSignedIn) {
    return <Navigate to="/login" replace />
  }
  return children
}
export default ProtectedRoute


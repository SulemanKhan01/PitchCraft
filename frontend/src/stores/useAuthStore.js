// ── JWT Auth Store (commented out — replaced by Clerk) ────────────────
// Clerk manages auth state now. This file is kept for future reference.
//
// import { create } from 'zustand'
// import { persist } from 'zustand/middleware'
//
// /* persist saves this store to localStorage automatically.
//    So even if the user refreshes the page, they stay logged in. */
// const useAuthStore = create(
//   persist(
//     (set) => ({
//       token: null,
//       user: null,       // { email: "..." }
//
//       setAuth: (token, user) => set({ token, user }),
//
//       logout: () => set({ token: null, user: null }),
//     }),
//     {
//       name: 'pitchcraft-auth',  // key saved in localStorage
//     }
//   )
// )
//
// export default useAuthStore

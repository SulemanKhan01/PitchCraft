const API_BASE = "http://localhost:8000"

/* ── OLD JWT auth helper (commented out) ──────────────────────────────
function authHeader() {
  const raw = localStorage.getItem('pitchcraft-auth')
  if (!raw) return {}
  try {
    const parsed = JSON.parse(raw)
    const token = parsed?.state?.token
    if (!token) return {}
    return { 'Authorization': `Bearer ${token}` }
  } catch {
    return {}
  }
}
─────────────────────────────────────────────────────────────────────── */

/* ── NEW Clerk auth helper ────────────────────────────────────────────
   Pass the Clerk token (from useAuth().getToken()) into each function.
   This keeps api.js as a plain JS file (no React hooks here).
─────────────────────────────────────────────────────────────────────── */
function authHeader(token) {
  if (!token) return {}
  return { 'Authorization': `Bearer ${token}` }
}

/* ══════════════════════════════════════════
   AUTH  (OLD — not needed with Clerk)
══════════════════════════════════════════ */

// export async function registerUser(email, password) { ... }  // handled by Clerk
// export async function loginUser(email, password) { ... }     // handled by Clerk

/* ══════════════════════════════════════════
   HEALTH
══════════════════════════════════════════ */

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/`)
  if (!res.ok) throw new Error('Backend is not running')
  return res.json()
}

/* ══════════════════════════════════════════
   UPLOAD
══════════════════════════════════════════ */

export async function uploadProposal(file, token) {
  const formData = new FormData()
  formData.append('file', file)

  const res = await fetch(`${API_BASE}/api/proposals/upload`, {
    method: 'POST',
    headers: { ...authHeader(token) },
    body: formData
  })

  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Upload failed')
  }
  return res.json()
}

/* ══════════════════════════════════════════
   CHAT
══════════════════════════════════════════ */

export async function sendChatMessage(question, history = [], token, previous_interaction_id = null) {
  const res = await fetch(`${API_BASE}/api/chat/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeader(token)
    },
    body: JSON.stringify({
      question,
      history,
      debug: false,
      previous_interaction_id
    })
  })

  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Chat request failed')
  }
  return res.json()
}

/* ══════════════════════════════════════════
   COVER LETTER
══════════════════════════════════════════ */

export async function generateCoverLetter(jdText, token) {
  const res = await fetch(`${API_BASE}/api/generate/cover-letter`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeader(token)
    },
    body: JSON.stringify({ jd_text: jdText })
  })

  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Cover letter generation failed')
  }
  return res.json()
}

export async function downloadCoverLetterPDF(text, token) {
  const res = await fetch(`${API_BASE}/api/generate/cover-letter/pdf`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeader(token)
    },
    body: JSON.stringify({ text })
  })

  if (!res.ok) throw new Error('PDF download failed')
  return res.blob()
}

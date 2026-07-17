const API_BASE = "http://localhost:8000"

/* ── Helper: read token from localStorage and build the auth header ── */
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

/* ══════════════════════════════════════════
   AUTH
══════════════════════════════════════════ */

export async function registerUser(email, password) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Registration failed')
  }
  return res.json()
}

export async function loginUser(email, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Login failed')
  }
  return res.json()  // { access_token, token_type, email }
}

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

export async function uploadProposal(file) {
  const formData = new FormData()
  formData.append('file', file)

  const res = await fetch(`${API_BASE}/api/proposals/upload`, {
    method: 'POST',
    headers: { ...authHeader() },  // token — no Content-Type for FormData
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

export async function sendChatMessage(question, history = []) {
  const res = await fetch(`${API_BASE}/api/chat/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeader()
    },
    body: JSON.stringify({ question, history, debug: false })
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

export async function generateCoverLetter(jdText) {
  const res = await fetch(`${API_BASE}/api/generate/cover-letter`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeader()
    },
    body: JSON.stringify({ jd_text: jdText })
  })

  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Cover letter generation failed')
  }
  return res.json()
}

export async function downloadCoverLetterPDF(text) {
  const res = await fetch(`${API_BASE}/api/generate/cover-letter/pdf`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeader()
    },
    body: JSON.stringify({ text })
  })

  if (!res.ok) throw new Error('PDF download failed')
  return res.blob()
}

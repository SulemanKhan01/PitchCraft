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

export async function uploadProposal(file, targetCollection, token) {
  const formData = new FormData()
  formData.append('file', file)

  const res = await fetch(`${API_BASE}/api/proposals/upload?target_collection=${targetCollection}`, {
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
   — now accepts conversation_id so the
     backend can auto-save messages to DB
══════════════════════════════════════════ */

export async function sendChatMessage(
  question,
  history = [],
  token,
  previous_interaction_id = null,
  conversation_id = null          // ← NEW: pass this to enable DB saving
) {
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
      previous_interaction_id,
      conversation_id              // ← NEW: included in every chat request
    })
  })

  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Chat request failed')
  }
  return res.json()
}

/* ══════════════════════════════════════════
   CONVERSATIONS
   — manage chat sessions in the database
══════════════════════════════════════════ */

/**
 * Create a new conversation session.
 * Call this once when the user opens the chat page.
 * Returns { id, title, created_at, updated_at }
 */
export async function createConversation(token) {
  const res = await fetch(`${API_BASE}/api/conversations/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeader(token)
    },
    body: JSON.stringify({ title: 'New Conversation' })
  })

  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Failed to create conversation')
  }
  return res.json()
}

/**
 * List all conversations for the current user (for sidebar).
 * Returns array of { id, title, created_at, updated_at }
 */
export async function listConversations(token) {
  const res = await fetch(`${API_BASE}/api/conversations/`, {
    method: 'GET',
    headers: { ...authHeader(token) }
  })

  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Failed to load conversations')
  }
  return res.json()
}

/**
 * Load a specific conversation with all its messages.
 * Returns { id, title, messages: [{ role, content, timestamp }] }
 */
export async function getConversation(conversationId, token) {
  const res = await fetch(`${API_BASE}/api/conversations/${conversationId}`, {
    method: 'GET',
    headers: { ...authHeader(token) }
  })

  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Failed to load conversation')
  }
  return res.json()
}

/**
 * Delete a conversation and all its messages.
 */
export async function deleteConversation(conversationId, token) {
  const res = await fetch(`${API_BASE}/api/conversations/${conversationId}`, {
    method: 'DELETE',
    headers: { ...authHeader(token) }
  })

  if (!res.ok && res.status !== 204) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to delete conversation')
  }
}

/* ══════════════════════════════════════════
   PROPOSAL GENERATION
══════════════════════════════════════════ */

/**
 * Generate a proposal by analyzing the full conversation from the DB.
 * Returns { proposal_content, requirements, web_search_used, message_count }
 */
export async function generateProposal(conversationId, token) {
  const res = await fetch(`${API_BASE}/api/generate/proposal`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeader(token)
    },
    body: JSON.stringify({ conversation_id: conversationId })
  })

  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Proposal generation failed')
  }
  return res.json()
}

/**
 * Download official AB {Ark} .docx proposal document.
 */
export async function downloadProposalDocx(conversationId, token) {
  const res = await fetch(`${API_BASE}/api/generate/proposal/docx`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeader(token)
    },
    body: JSON.stringify({ conversation_id: conversationId })
  })

  if (!res.ok) {
    throw new Error('Failed to download DOCX proposal')
  }

  const blob = await res.blob()
  return blob
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

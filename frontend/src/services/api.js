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
  conversation_id = null,
  options = {}
) {
  const headers = {
    'Content-Type': 'application/json',
    ...authHeader(token)
  }
  if (options.tavilyApiKey) {
    headers['X-Tavily-Key'] = options.tavilyApiKey
  }
  if (options.aiModel) {
    headers['X-AI-Model'] = options.aiModel
  }

  const res = await fetch(`${API_BASE}/api/chat/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      question,
      history,
      debug: !!options.debugMode,
      previous_interaction_id,
      conversation_id,
      score_threshold: options.scoreThreshold,
      max_chunks: options.maxChunks,
      web_search: options.webSearchEnabled !== false
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

export async function generateProposal(conversationId, token, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...authHeader(token)
  }
  if (options.aiModel) headers['X-AI-Model'] = options.aiModel

  const res = await fetch(`${API_BASE}/api/generate/proposal`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      conversation_id: conversationId,
      writing_tone: options.writingTone,
      agency_name: options.agencyName,
      portfolio_url: options.portfolioUrl
    })
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

export async function generateCoverLetter(jdText, token, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...authHeader(token)
  }
  if (options.aiModel) headers['X-AI-Model'] = options.aiModel

  const res = await fetch(`${API_BASE}/api/generate/cover-letter`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      jd_text: jdText,
      writing_tone: options.writingTone,
      agency_name: options.agencyName,
      portfolio_url: options.portfolioUrl,
      signature_text: options.signatureText
    })
  })

  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Cover letter generation failed')
  }
  return res.json()
}

export async function downloadCoverLetterPDF(text, token, options = {}) {
  const res = await fetch(`${API_BASE}/api/generate/cover-letter/pdf`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeader(token)
    },
    body: JSON.stringify({
      text,
      pdf_template: options.pdfTemplate || 'minimalist'
    })
  })

  if (!res.ok) throw new Error('PDF download failed')
  return res.blob()
}


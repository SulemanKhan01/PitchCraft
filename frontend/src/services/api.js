// In development: http://localhost:8000
// In production: "" (empty = relative URL, Nginx handles /api/* routing)
const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000"

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
export async function downloadProposalDocx(conversationId, proposalContent, token) {
  const res = await fetch(`${API_BASE}/api/generate/proposal/docx`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeader(token)
    },
    body: JSON.stringify({
      conversation_id: conversationId,
      proposal_content: proposalContent
    })
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

export async function downloadCoverLetterDocx(text, token) {
  const res = await fetch(`${API_BASE}/api/generate/cover-letter/docx`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeader(token)
    },
    body: JSON.stringify({ text })
  })

  if (!res.ok) throw new Error('DOCX download failed')
  return res.blob()
}

/* ══════════════════════════════════════════
   WEBSITE GENERATOR & DEPLOYMENT
══════════════════════════════════════════ */

/**
 * Generates and deploys a demo static website based on job description.
 * @param {string} jobDescription - Client job description or website brief
 * @param {string} customInstructions - Optional extra styling/feature instructions
 * @param {string} token - Clerk authorization token
 * @returns {Promise<{status: string, public_url: string, site_title: string, site_id: string}>}
 */
export async function generateAndDeployWebsite(jobDescription, customInstructions = '', token) {
  const res = await fetch(`${API_BASE}/api/generate/website`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeader(token)
    },
    body: JSON.stringify({
      job_description: jobDescription,
      custom_instructions: customInstructions
    })
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Website generation and deployment failed')
  }

  return res.json()
}

/* ══════════════════════════════════════════
   UPWORK JOBS MANAGEMENT
══════════════════════════════════════════ */

/**
 * Triggers the Upwork scraping pipeline on the backend and saves new jobs to DB.
 */
export async function triggerJobScraper(token) {
  const res = await fetch(`${API_BASE}/api/jobs/scrape`, {
    method: 'POST',
    headers: { ...authHeader(token) }
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Scraper failed to run')
  }

  return res.json()
}

/**
 * List all saved jobs for the user from DB.
 */
export async function listJobs(token) {
  const res = await fetch(`${API_BASE}/api/jobs/`, {
    method: 'GET',
    headers: { ...authHeader(token) }
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to fetch jobs')
  }

  return res.json()
}

/**
 * Toggle job status between "pending" and "applied".
 */
export async function updateJobStatus(jobId, status, token) {
  const res = await fetch(`${API_BASE}/api/jobs/${jobId}/status`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      ...authHeader(token)
    },
    body: JSON.stringify({ status })
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to update job status')
  }

  return res.json()
}

/**
 * Delete a job by ID.
 */
export async function deleteJob(jobId, token) {
  const res = await fetch(`${API_BASE}/api/jobs/${jobId}`, {
    method: 'DELETE',
    headers: { ...authHeader(token) }
  })

  if (!res.ok && res.status !== 204) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to delete job')
  }
}

/* ── NEW: Auto-scraper Scheduler Status ───────────────────────────────────── */

/**
 * Get the APScheduler state: next_scrape_at, last_scraped_at, is_running.
 * No auth token needed — public status endpoint.
 */
export async function getScraperStatus() {
  const res = await fetch(`${API_BASE}/api/jobs/scraper-status`, {
    method: 'GET',
  })

  if (!res.ok) {
    throw new Error('Failed to fetch scraper status')
  }

  return res.json()
}

/* ============================================
   API Helper Module
   ============================================

   CONCEPT: Centralized API Communication

   This module handles ALL communication with the FastAPI backend.
   Every function:
   1. Creates a request (with correct headers/body)
   2. Sends it with fetch()
   3. Handles errors
   4. Returns parsed JSON

   WHY centralize? If the API URL changes, you update ONE file.
   If you need to add auth headers later, you add it ONE time.

   BASE URL: http://localhost:8000 (FastAPI dev server)
   ============================================ */

const API_BASE = "http://localhost:8000"
const WS_BASE = "ws://localhost:8000"

/* ============================================
   CONCEPT: WebSocket Connection

   HTTP:  Browser opens connection → sends request → gets response → connection closes
   WS:    Browser opens connection → stays open → both sides send messages freely

   Creating a WebSocket:
     new WebSocket("ws://localhost:8000/ws/chat")

   WebSocket events:
     ws.onopen    = function() { }        // Connection established
     ws.onmessage = function(event) { }   // Received a message from server
     ws.onclose   = function() { }        // Connection closed
     ws.onerror   = function() { }        // Something went wrong

   Sending a message:
     ws.send(JSON.stringify({ question: "hello" }))

   The server can send messages at ANY time after the connection is open.
   This is what makes streaming possible — server sends tokens as they're ready.
   ============================================ */

/* ============================================
   CONCEPT: fetch() API

   fetch() is the browser's built-in HTTP client.
   It returns a Promise that resolves to a Response object.

   Basic pattern:
     const response = await fetch(url, options)
     const data = await response.json()    // Parse JSON body

   OPTIONS object:
     method:  "GET" | "POST" | "PUT" | "DELETE"
     headers: { "Content-Type": "application/json" }
     body:    JSON.stringify(data)  ← for JSON
              or FormData           ← for file uploads
   ============================================ */

/**
 * Health check — verifies backend is running
 */
export async function checkHealth() {
  const res = await fetch(`${API_BASE}/`)
  if (!res.ok) throw new Error("Backend is not running")
  return res.json()
}

/**
 * Upload a PDF proposal to the knowledge base
 *
 * CONCEPT: FormData for file uploads
 *
 * Files can't be sent as JSON. Instead, we use FormData,
 * which wraps the file in a special multipart format:
 *
 * Content-Type: multipart/form-data; boundary=----WebKitFormBoundary...
 * ------WebKitFormBoundary...
 * Content-Disposition: form-data; name="file"; filename="proposal.pdf"
 * Content-Type: application/pdf
 * <binary file data>
 * ------WebKitFormBoundary...--
 *
 * The browser sets the correct Content-Type header automatically
 * when you pass FormData as the body — do NOT set it manually!
 */
export async function uploadProposal(file) {
  const formData = new FormData()
  formData.append("file", file)  // "file" must match the backend parameter name

  const res = await fetch(`${API_BASE}/api/proposals/upload`, {
    method: "POST",
    body: formData
    // NOTE: Do NOT set Content-Type header!
    // fetch() auto-sets it with the correct boundary when body is FormData
  })

  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || "Upload failed")
  }
  return res.json()
}

/**
 * Send a chat message and get an AI response
 *
 * CONCEPT: JSON request body
 *
 * For non-file data, we send JSON:
 *   Content-Type: application/json
 *   Body: {"question": "What is the budget?", "history": []}
 */
// export async function sendChatMessage(question, history = []) {
//   const res = await fetch(`${API_BASE}/api/chat/chat`, {
//     method: "POST",
//     headers: {
//       "Content-Type": "application/json"
//     },
//     body: JSON.stringify({
//       question,
//       history,
//       debug: false
//     })
//   })

//   if (!res.ok) {
//     const err = await res.json()
//     throw new Error(err.detail || "Chat request failed")
//   }
//   return res.json()
// }

/**
 * Generate a cover letter from a job description
 */
export async function generateCoverLetter(jdText) {
  const res = await fetch(`${API_BASE}/api/generate/cover-letter`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ jd_text: jdText })
  })

  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || "Cover letter generation failed")
  }
  return res.json()
}

/**
 * Download cover letter as PDF
 *
 * CONCEPT: Binary response (Blob)
 *
 * PDFs are binary data, not text. We use response.blob()
 * to get the raw bytes, then create a downloadable URL.
 */
export async function downloadCoverLetterPDF(text) {
  const res = await fetch(`${API_BASE}/api/generate/cover-letter/pdf`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ text })
  })

  if (!res.ok) {
    throw new Error("PDF download failed")
  }

  // Returns raw binary data (the PDF file)
  return res.blob()
}

/**
 * Open a WebSocket connection for streaming chat
 *
 * CONCEPT: WebSocket Streaming
 *
 * Instead of waiting for the full AI response (which can take 5-10 seconds),
 * we open a WebSocket connection. The server sends tokens one by one as they're
 * generated. This is how ChatGPT-like apps give the "typing" effect.
 *
 * This function returns a "controller" object with:
 *   - send(question, history) — sends a message to the server
 *   - close() — closes the connection
 *   - onToken(callback) — register a callback for each incoming token
 *   - onDone(callback) — register a callback when response is complete
 *   - onError(callback) — register a callback for errors
 *
 * The callbacks pattern lets ChatPage react to streaming events:
 *   onToken(text => setReply(prev => prev + text))  → append each token
 *   onDone(() => setIsLoading(false))                → stop loading state
 */
export function createChatStream({ onToken, onDone, onError }) {
  // Step 1: Create the WebSocket connection
  const ws = new WebSocket(`${WS_BASE}/ws/chat`)

  // Step 2: Register event handlers

  // onopen — connection is ready, we can now send messages
  ws.onopen = () => {
    console.log("WebSocket connected")
  }

  // onmessage — server sent us something
  ws.onmessage = (event) => {
    // event.data is a JSON string — parse it to get the object
    const data = JSON.parse(event.data)

    if (data.type === "token") {
      // A piece of the AI response — pass it to the token callback
      onToken?.(data.content)
    } else if (data.type === "done") {
      // The full response has been sent
      onDone?.()
    } else if (data.type === "error") {
      onError?.(data.content)
    }
  }

  // onerror — something went wrong with the connection
  ws.onerror = (error) => {
    console.error("WebSocket error:", error)
    onError?.("Connection error")
  }

  // onclose — connection was closed (by server or network)
  ws.onclose = () => {
    console.log("WebSocket closed")
  }

  // Step 3: Return a controller object
  // This is a CLEAN API — ChatPage doesn't need to know about WebSocket internals
  return {
    // Send a message to the server
    send(question, history = []) {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ question, history }))
      }
    },

    // Close the connection
    close() {
      ws.close()
    }
  }
}

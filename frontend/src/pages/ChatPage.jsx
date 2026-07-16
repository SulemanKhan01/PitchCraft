/* ============================================
   Chat Page — WebSocket Streaming
   ============================================

   CONCEPT: Real-Time Streaming with WebSocket

   BEFORE (fetch): User asks → waits 5-10s → entire answer appears at once
   AFTER (WebSocket): User asks → answer types itself word by word

   HOW IT WORKS:
   1. Component mounts → opens WebSocket connection (stays open)
   2. User sends message → WebSocket sends it to server
   3. Server streams tokens back → each token triggers onToken callback
   4. onToken appends text to the current message → React re-renders
   5. Server sends "done" → onDone stops the loading state

   KEY DIFFERENCE FROM FETCH:
   - fetch() is request-response (one shot)
   - WebSocket is a persistent pipe (continuous flow)

   NEW CONCEPTS:
   - useRef to hold the WebSocket controller across renders
   - useEffect to open/close connection on mount/unmount
   - Incremental state updates (appending to a string, not replacing)
   ============================================ */

import { useState, useRef, useEffect } from 'react'
import { createChatStream } from '../services/api'
import './Pages.css'

function ChatPage() {
  /* STATE: Array of messages (same as before) */
  const [messages, setMessages] = useState([])

  /* STATE: The text currently being streamed (the "typing" message)
     This is DIFFENT from messages — it's the incomplete response
     that's still being received token by token. */
  const [streamingText, setStreamingText] = useState('')

  /* STATE: Input field */
  const [input, setInput] = useState('')

  /* STATE: Loading indicator */
  const [isLoading, setIsLoading] = useState(false)

  /* REF: Auto-scroll anchor */
  const messagesEndRef = useRef(null)

  /* REF: Textarea for auto-resize */
  const textareaRef = useRef(null)

  /* REF: Holds the WebSocket controller
     useRef (not useState) because we don't want re-renders when this changes.
     We just need a stable reference to call .send() and .close() on. */
  const wsRef = useRef(null)

  /* ============================================
     EFFECT: Open WebSocket on mount, close on unmount

     useEffect with empty dependency array [] runs ONCE when component mounts.
     The cleanup function (return) runs when component unmounts.

     This ensures:
     - Connection opens when user visits Chat page
     - Connection closes when user navigates away (frees resources)
     ============================================ */
  useEffect(() => {
    let cancelled = false

    wsRef.current = createChatStream({
      /* onToken: Called for each token the server sends.
         We APPEND to streamingText — this is how the text "types itself". */
      onToken: (token) => {
        if (!cancelled) setStreamingText(prev => prev + token)
      },

      /* onDone: Server finished sending the full response.
         Move the streaming text into the messages array as a complete message. */
      onDone: () => {
        if (!cancelled) {
          setStreamingText(prevText => {
            if (prevText) {
              setMessages(p => [...p, { role: 'assistant', content: prevText }])
            }
            return ''
          })
          setIsLoading(false)
        }
      },

      /* onError: Something went wrong */
      onError: (errorMsg) => {
        if (!cancelled) {
          setStreamingText(() => {
            setMessages(p => [...p, {
              role: 'assistant',
              content: `Error: ${errorMsg}`
            }])
            return ''
          })
          setIsLoading(false)
        }
      }
    })

    // Cleanup: close WebSocket when component unmounts
    return () => {
      cancelled = true
      wsRef.current?.close()
    }
  }, [])  // [] = run only on mount

  /* Auto-scroll when messages or streaming text changes */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingText])

  /* Auto-resize textarea */
  function handleInputChange(event) {
    setInput(event.target.value)
    const textarea = event.target
    textarea.style.height = 'auto'
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px'
  }

  /* Enter to send */
  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSend()
    }
  }

  /* Send message via WebSocket */
  function handleSend() {
    const question = input.trim()
    if (!question || isLoading) return

    // Add user message to the list
    setMessages(prev => [...prev, { role: 'user', content: question }])
    setInput('')
    setIsLoading(true)
    setStreamingText('')  // Clear any previous streaming text

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }

    // Build history for conversation context
    const history = [...messages, { role: 'user', content: question }].map(msg => ({
      role: msg.role,
      content: msg.content
    }))

    // Send via WebSocket (not fetch!)
    wsRef.current?.send(question, history)
  }

  return (
    <div className="page" style={{ height: '100%' }}>
      <div className="page-header">
        <h1 className="page-title">Chat with Proposals</h1>
        <p className="page-subtitle">
          Ask questions about your uploaded proposals and get AI-powered answers.
        </p>
      </div>

      <div className="chat-container">
        <div className="chat-messages">
          {/* Empty state */}
          {messages.length === 0 && !streamingText && (
            <div className="chat-empty">
              <div className="chat-empty-icon">💬</div>
              <h3>Ask anything about your proposals</h3>
              <p>e.g., "What's the budget for the AI project?"</p>
            </div>
          )}

          {/* Render completed messages */}
          {messages.map((msg, index) => (
            <div key={index} className={`chat-message ${msg.role}`}>
              <div className="chat-avatar">
                {msg.role === 'user' ? '👤' : '🤖'}
              </div>
              <div className="chat-bubble">
                {msg.content}
              </div>
            </div>
          ))}

          {/* STREAMING MESSAGE — text appears token by token
              This is the key difference from the fetch version!
              Instead of a loading spinner, the user sees the actual text
              being "typed" in real-time. */}
          {streamingText && (
            <div className="chat-message assistant">
              <div className="chat-avatar">🤖</div>
              <div className="chat-bubble">
                {streamingText}
                {/* Blinking cursor while streaming */}
                <span className="streaming-cursor">|</span>
              </div>
            </div>
          )}

          {/* Loading dots — only show before first token arrives */}
          {isLoading && !streamingText && (
            <div className="chat-message assistant">
              <div className="chat-avatar">🤖</div>
              <div className="chat-bubble">
                <div className="chat-typing">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="chat-input-area">
          <div className="chat-input-row">
            <textarea
              ref={textareaRef}
              className="chat-input"
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your proposals..."
              rows={1}
              disabled={isLoading}
            />
            <button
              className="chat-send-btn"
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatPage

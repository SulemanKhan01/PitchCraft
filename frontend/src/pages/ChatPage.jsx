import { useRef, useEffect, useState } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { sendChatMessage } from '../services/api'
import useChatStore from '../stores/useChatStore'
import './ChatPage.css'

/* ── tiny sparkle icon ── */
const SparkleIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
    <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17 5.8 21.3l2.4-7.4L2 9.4h7.6z"/>
  </svg>
)

/* ── paper-plane send icon ── */
const SendIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
       strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <line x1="22" y1="2" x2="11" y2="13"/>
    <polygon points="22 2 15 22 11 13 2 9 22 2"/>
  </svg>
)

/* ── clip icon ── */
const ClipIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
       strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"/>
  </svg>
)

const SUGGESTIONS = [
  { label: "Budget overview", text: "What's the budget for the AI project?" },
  { label: "Key deliverables", text: "Summarize the key deliverables" },
  { label: "Project timeline", text: "What are the project timelines?" },
  { label: "Stakeholders", text: "Who are the main stakeholders?" },
  { label: "Risk factors", text: "What are the main risk factors?" },
  { label: "Tech stack", text: "What technology stack is proposed?" },
]

function ChatPage() {
  const messages   = useChatStore((s) => s.messages)
  const input      = useChatStore((s) => s.input)
  const isLoading  = useChatStore((s) => s.isLoading)
  const setInput   = useChatStore((s) => s.setInput)
  const setIsLoading = useChatStore((s) => s.setIsLoading)
  const addMessage = useChatStore((s) => s.addMessage)

  const messagesEndRef = useRef(null)
  const textareaRef    = useRef(null)
  const [focused, setFocused] = useState(false)
  const { getToken } = useAuth()

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  function handleInputChange(e) {
    setInput(e.target.value)
    const ta = e.target
    ta.style.height = 'auto'
    ta.style.height = Math.min(ta.scrollHeight, 160) + 'px'
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  async function handleSend() {
    const { messages: cur, isLoading: busy } = useChatStore.getState()
    const q = input.trim()
    if (!q || busy) return

    const userMsg = { role: 'user', content: q }
    addMessage(userMsg)
    setInput('')
    setIsLoading(true)
    if (textareaRef.current) textareaRef.current.style.height = 'auto'

    try {
      const history = [...cur, userMsg].map(m => ({ role: m.role, content: m.content }))
      const token   = await getToken()
      const result  = await sendChatMessage(q, history, token)
      addMessage({ role: 'assistant', content: result.answer })
    } catch (err) {
      addMessage({ role: 'assistant', content: `Something went wrong: ${err.message}` })
    } finally {
      setIsLoading(false)
    }
  }

  function pickSuggestion(text) {
    setInput(text)
    textareaRef.current?.focus()
  }

  const isEmpty = messages.length === 0

  return (
    <div className="cp-root">

      {/* ── Top bar ── */}
      <header className="cp-topbar">
        <div className="cp-topbar-content">
          <div className="cp-topbar-left">
            <div className="cp-topbar-icon">
              <SparkleIcon />
            </div>
            <div>
              <div className="cp-topbar-title">PitchCraft AI</div>
              <div className="cp-topbar-status">
                <span className="cp-status-dot" />
                Ready to help
              </div>
            </div>
          </div>
          <div className="cp-topbar-right">
            <button className="cp-icon-btn" title="Clear conversation" type="button">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"/>
              </svg>
            </button>
            <button className="cp-icon-btn" title="Export chat" type="button">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* ── Messages Viewport (Scroll Container) ── */}
      <div className="cp-messages-viewport">
        <div className="cp-messages-container">

          {/* Empty state */}
          {isEmpty && (
            <div className="cp-empty">
              <div className="cp-empty-glow" />
              <div className="cp-empty-orb">
                <div className="cp-empty-ring cp-empty-ring--1" />
                <div className="cp-empty-ring cp-empty-ring--2" />
                <div className="cp-empty-orb-core">
                  <SparkleIcon />
                </div>
                <div className="cp-empty-dot" />
              </div>

              <h2 className="cp-empty-title">Ask anything about your proposals</h2>
              <p className="cp-empty-desc">
                I can analyse budgets, timelines, stakeholders, and more from your uploaded documents.
              </p>

              <div className="cp-chips">
                {SUGGESTIONS.map((s, i) => (
                  <button key={i} className="cp-chip" onClick={() => pickSuggestion(s.text)} type="button">
                    <span className="cp-chip-label">{s.label}</span>
                    <span className="cp-chip-text">{s.text}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Message list */}
          {messages.map((msg, i) => (
            <div key={i} className={`cp-msg cp-msg--${msg.role}`}>
              {msg.role === 'assistant' && (
                <div className="cp-avatar cp-avatar--ai" aria-label="AI">
                  <SparkleIcon />
                </div>
              )}
              <div className="cp-bubble">
                <p className="cp-bubble-text">{msg.content}</p>
              </div>
              {msg.role === 'user' && (
                <div className="cp-avatar cp-avatar--user" aria-label="You">AS</div>
              )}
            </div>
          ))}

          {/* Typing indicator */}
          {isLoading && (
            <div className="cp-msg cp-msg--assistant">
              <div className="cp-avatar cp-avatar--ai">
                <SparkleIcon />
              </div>
              <div className="cp-bubble cp-bubble--typing">
                <span /><span /><span />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="cp-input-outer">
        <div className="cp-input-inner">
          <div className={`cp-input-shell${focused ? ' cp-input-shell--focused' : ''}`}>
            <textarea
              ref={textareaRef}
              className="cp-textarea"
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              placeholder="Ask about your proposals…"
              rows={1}
              disabled={isLoading}
            />
            <div className="cp-input-tools">
              <button className="cp-tool-btn" title="Attach file" type="button">
                <ClipIcon />
              </button>
              <div className="cp-input-divider" />
              <button
                className="cp-send-btn"
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                type="button"
                title="Send (Enter)"
              >
                <SendIcon />
                <span>Send</span>
              </button>
            </div>
          </div>
          <p className="cp-hint">Press <kbd>Enter</kbd> to send · <kbd>Shift+Enter</kbd> for new line</p>
        </div>
      </div>

    </div>
  )
}

export default ChatPage

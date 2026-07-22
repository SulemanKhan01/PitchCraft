/**
 * ChatPage.jsx — PitchCraft AI Chat
 *
 * REDESIGN GUARDRAILS (strictly enforced):
 *  - All API calls, store bindings, and event handlers are 100% preserved.
 *  - No changes to useChatStore.js, api.js, or any backend contract.
 *  - Only the presentation layer (JSX + CSS) is enhanced.
 *  - Skill guidelines applied: Glassmorphism dark, WCAG AA contrast,
 *    44×44px touch targets, reduced-motion respect, full keyboard nav.
 */

import { useRef, useEffect, useState, useCallback } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { sendChatMessage } from '../services/api'
import useChatStore from '../stores/useChatStore'
import './ChatPage.css'

/* ─────────────────────────────────────────────────────────────────────────────
   SVG ICON COMPONENTS — aria-hidden, no emoji substitutes (skill rule #4)
───────────────────────────────────────────────────────────────────────────── */

const SparkleIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">
    <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17 5.8 21.3l2.4-7.4L2 9.4h7.6z" />
  </svg>
)

const SendIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
    strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
    <line x1="22" y1="2" x2="11" y2="13" />
    <polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
)

const ClipIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
    strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
    <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" />
  </svg>
)

const CopyIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
    strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
    <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
    <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
  </svg>
)

const ThumbUpIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
    strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
    <path d="M14 9V5a3 3 0 00-3-3l-4 9v11h11.28a2 2 0 002-1.7l1.38-9a2 2 0 00-2-2.3H14z" />
    <path d="M7 22H4a2 2 0 01-2-2v-7a2 2 0 012-2h3" />
  </svg>
)

const ThumbDownIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
    strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
    <path d="M10 15v4a3 3 0 003 3l4-9V2H5.72a2 2 0 00-2 1.7l-1.38 9a2 2 0 002 2.3H10z" />
    <path d="M17 2h2.67A2.31 2.31 0 0122 4v7a2.31 2.31 0 01-2.33 2H17" />
  </svg>
)

const RefreshIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
    strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
    <polyline points="23 4 23 10 17 10" />
    <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10" />
  </svg>
)

const ChevronDownIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
    strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
    <polyline points="6 9 12 15 18 9" />
  </svg>
)

const TrashIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
    strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
    <polyline points="3 6 5 6 21 6" />
    <path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" />
    <path d="M10 11v6M14 11v6" />
    <path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2" />
  </svg>
)

const ExportIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
    strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
    <polyline points="7 10 12 15 17 10" />
    <line x1="12" y1="15" x2="12" y2="3" />
  </svg>
)

/* ─────────────────────────────────────────────────────────────────────────────
   SUGGESTION CHIPS — unchanged from original, just referenced below
───────────────────────────────────────────────────────────────────────────── */

const SUGGESTIONS = [
  { label: 'Budget Overview', text: "What's the budget for the AI project?", icon: '💰' },
  { label: 'Key Deliverables', text: 'Summarize the key deliverables', icon: '📋' },
  { label: 'Project Timeline', text: 'What are the project timelines?', icon: '📅' },
  { label: 'Stakeholders', text: 'Who are the main stakeholders?', icon: '👥' },
  { label: 'Risk Factors', text: 'What are the main risk factors?', icon: '⚠️' },
  { label: 'Tech Stack', text: 'What technology stack is proposed?', icon: '⚙️' },
]

/* ─────────────────────────────────────────────────────────────────────────────
   MESSAGE ACTION TOOLBAR — Copy / Retry / Feedback per bubble
   Props:
     content  : string  — message text to copy
     onRetry? : fn      — retry handler (assistant messages only)
───────────────────────────────────────────────────────────────────────────── */

function MessageActions({ content, onRetry }) {
  const [copied, setCopied] = useState(false)
  const [feedback, setFeedback] = useState(null) // 'up' | 'down' | null

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(content).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }, [content])

  return (
    <div className="cp-msg-actions" role="toolbar" aria-label="Message actions">
      {/* Copy */}
      <button
        className={`cp-action-btn${copied ? ' cp-action-btn--done' : ''}`}
        onClick={handleCopy}
        aria-label={copied ? 'Copied!' : 'Copy message'}
        title={copied ? 'Copied!' : 'Copy'}
        type="button"
      >
        <CopyIcon />
        <span className="cp-action-label">{copied ? 'Copied!' : 'Copy'}</span>
      </button>

      {/* Retry — only for assistant messages */}
      {onRetry && (
        <button
          className="cp-action-btn"
          onClick={onRetry}
          aria-label="Retry response"
          title="Retry"
          type="button"
        >
          <RefreshIcon />
          <span className="cp-action-label">Retry</span>
        </button>
      )}

      {/* Thumbs up / down feedback */}
      {onRetry && (
        <>
          <div className="cp-action-divider" aria-hidden="true" />
          <button
            className={`cp-action-btn${feedback === 'up' ? ' cp-action-btn--active' : ''}`}
            onClick={() => setFeedback(f => f === 'up' ? null : 'up')}
            aria-label="Good response"
            aria-pressed={feedback === 'up'}
            title="Good response"
            type="button"
          >
            <ThumbUpIcon />
          </button>
          <button
            className={`cp-action-btn${feedback === 'down' ? ' cp-action-btn--active' : ''}`}
            onClick={() => setFeedback(f => f === 'down' ? null : 'down')}
            aria-label="Bad response"
            aria-pressed={feedback === 'down'}
            title="Bad response"
            type="button"
          >
            <ThumbDownIcon />
          </button>
        </>
      )}
    </div>
  )
}

/* ─────────────────────────────────────────────────────────────────────────────
   SCROLL-TO-BOTTOM FAB — appears when user has scrolled up
───────────────────────────────────────────────────────────────────────────── */

function ScrollToBottomBtn({ visible, onClick }) {
  return (
    <button
      className={`cp-scroll-fab${visible ? ' cp-scroll-fab--visible' : ''}`}
      onClick={onClick}
      aria-label="Scroll to latest message"
      title="Scroll to bottom"
      type="button"
      tabIndex={visible ? 0 : -1}
    >
      <ChevronDownIcon />
    </button>
  )
}

/* ─────────────────────────────────────────────────────────────────────────────
   MAIN CHAT PAGE COMPONENT
───────────────────────────────────────────────────────────────────────────── */

function ChatPage() {
  /* ── Store bindings — UNCHANGED ── */
  const messages = useChatStore((s) => s.messages)
  const input = useChatStore((s) => s.input)
  const isLoading = useChatStore((s) => s.isLoading)
  const setInput = useChatStore((s) => s.setInput)
  const setIsLoading = useChatStore((s) => s.setIsLoading)
  const addMessage = useChatStore((s) => s.addMessage)
  const clearChat = useChatStore((s) => s.clearChat)

  /* ── Refs & local UI state ── */
  const messagesEndRef = useRef(null)
  const viewportRef = useRef(null)
  const textareaRef = useRef(null)

  const [focused, setFocused] = useState(false)
  const [showScrollFab, setShowScrollFab] = useState(false)
  const [charCount, setCharCount] = useState(0)

  const [interactionId, setInteractionId] = useState(null)


  const { getToken } = useAuth()

  /* ── Auto-scroll: follows new messages — PRESERVED ── */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  /* ── Scroll FAB visibility — shows when user scrolls up ── */
  const handleViewportScroll = useCallback(() => {
    const el = viewportRef.current
    if (!el) return
    const distFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
    setShowScrollFab(distFromBottom > 120)
  }, [])

  useEffect(() => {
    const el = viewportRef.current
    if (!el) return
    el.addEventListener('scroll', handleViewportScroll, { passive: true })
    return () => el.removeEventListener('scroll', handleViewportScroll)
  }, [handleViewportScroll])

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  /* ── Input auto-grow — PRESERVED ── */
  const handleInputChange = useCallback((e) => {
    setInput(e.target.value)
    setCharCount(e.target.value.length)
    const ta = e.target
    ta.style.height = 'auto'
    ta.style.height = Math.min(ta.scrollHeight, 160) + 'px'
  }, [setInput])

  /* ── Keyboard: Enter = send, Shift+Enter = newline — PRESERVED ── */
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
    // Escape clears focus
    if (e.key === 'Escape') {
      textareaRef.current?.blur()
    }
  }, [input]) // eslint-disable-line react-hooks/exhaustive-deps

  /* ── Send message — API contract UNCHANGED ── */
  async function handleSend() {
    const { messages: cur, isLoading: busy } = useChatStore.getState()
    const q = input.trim()
    if (!q || busy) return

    const userMsg = { role: 'user', content: q }
    addMessage(userMsg)
    setInput('')
    setCharCount(0)
    setIsLoading(true)
    if (textareaRef.current) textareaRef.current.style.height = 'auto'

    try {
      const history = [...cur, userMsg].map(m => ({ role: m.role, content: m.content }))
      const token = await getToken()
      const result = await sendChatMessage(q, history, token, interactionId)
      if (result.interaction_id) {
        setInteractionId(result.interaction_id)
      }
      addMessage({ role: 'assistant', content: result.answer })

    } catch (err) {
      addMessage({ role: 'assistant', content: `Something went wrong: ${err.message}` })
    } finally {
      setIsLoading(false)
    }
  }

  /* ── Suggestion chip click — PRESERVED ── */
  const pickSuggestion = useCallback((text) => {
    setInput(text)
    setCharCount(text.length)
    textareaRef.current?.focus()
    // Trigger auto-grow for prefilled text
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height =
        Math.min(textareaRef.current.scrollHeight, 160) + 'px'
    }
  }, [setInput])

  /* ── Retry last assistant message ── */
  const handleRetry = useCallback(async (index) => {
    // Find the user message that preceded this assistant message
    const precedingUser = messages.slice(0, index).reverse().find(m => m.role === 'user')
    if (!precedingUser) return

    const { messages: cur } = useChatStore.getState()
    setIsLoading(true)
    try {
      const history = cur.slice(0, index).map(m => ({ role: m.role, content: m.content }))
      const token = await getToken()
      const result = await sendChatMessage(precedingUser.content, history, token)
      // Replace the assistant message at that index
      const updated = [...cur]
      updated[index] = { role: 'assistant', content: result.answer }
      useChatStore.getState().setMessages(updated)
    } catch (err) {
      const updated = [...cur]
      updated[index] = { role: 'assistant', content: `Retry failed: ${err.message}` }
      useChatStore.getState().setMessages(updated)
    } finally {
      setIsLoading(false)
    }
  }, [messages, getToken, setIsLoading])

  /* ── Handle clear conversation ── */
  const handleClear = useCallback(() => {
    if (messages.length === 0) return
    if (window.confirm('Clear this conversation?')) {
      clearChat()
      setInteractionId(null)
    }
  }, [messages.length, clearChat])


  const isEmpty = messages.length === 0

  /* ── Format timestamp ── */
  const now = new Date()
  const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

  /* ─────────────────────────────────────────────────────────────────────────
     RENDER
  ──────────────────────────────────────────────────────────────────────────*/
  return (
    <div className="cp-root" role="main" aria-label="PitchCraft AI Chat">

      {/* ── Ambient background glow layers ── */}
      <div className="cp-bg-glow cp-bg-glow--1" aria-hidden="true" />
      <div className="cp-bg-glow cp-bg-glow--2" aria-hidden="true" />

      {/* ────────────────────────────────────────────────────────────────────
          TOP BAR — sticky header with AI identity & quick actions
      ─────────────────────────────────────────────────────────────────────*/}
      <header className="cp-topbar" role="banner">
        <div className="cp-topbar-content">

          {/* Left: AI Brand */}
          <div className="cp-topbar-left">
            <div className="cp-topbar-orb" aria-hidden="true">
              <SparkleIcon />
              <span className="cp-orb-pulse" />
            </div>
            <div className="cp-topbar-info">
              <div className="cp-topbar-title">PitchCraft AI</div>
              <div className="cp-topbar-status">
                <span className="cp-status-dot" aria-hidden="true" />
                <span>Ready to help</span>
              </div>
            </div>
          </div>

          {/* Right: Actions */}
          <div className="cp-topbar-right">
            {/* Message count badge */}
            {!isEmpty && (
              <span className="cp-msg-count" aria-live="polite" aria-label={`${messages.length} messages`}>
                {messages.length} msg{messages.length !== 1 ? 's' : ''}
              </span>
            )}
            <button
              className="cp-icon-btn"
              onClick={handleClear}
              title="Clear conversation"
              aria-label="Clear conversation"
              type="button"
            >
              <TrashIcon />
            </button>
            <button
              className="cp-icon-btn"
              title="Export chat"
              aria-label="Export chat"
              type="button"
            >
              <ExportIcon />
            </button>
          </div>
        </div>

        {/* Progress bar while loading */}
        <div className={`cp-topbar-progress${isLoading ? ' cp-topbar-progress--active' : ''}`} aria-hidden="true" />
      </header>

      {/* ────────────────────────────────────────────────────────────────────
          MESSAGES VIEWPORT — scrollable area
      ─────────────────────────────────────────────────────────────────────*/}
      <div
        className="cp-messages-viewport"
        ref={viewportRef}
        role="log"
        aria-label="Conversation"
        aria-live="polite"
        aria-relevant="additions"
      >
        <div className="cp-messages-container">

          {/* ── EMPTY STATE ── */}
          {isEmpty && (
            <div className="cp-empty" aria-label="Start a conversation">
              {/* Decorative glow */}
              <div className="cp-empty-glow" aria-hidden="true" />

              {/* Animated orb */}
              <div className="cp-empty-orb" aria-hidden="true">
                <div className="cp-empty-ring cp-empty-ring--1" />
                <div className="cp-empty-ring cp-empty-ring--2" />
                <div className="cp-empty-ring cp-empty-ring--3" />
                <div className="cp-empty-orb-core">
                  <SparkleIcon />
                </div>
                <div className="cp-empty-dot" />
              </div>

              <h1 className="cp-empty-title">Ask anything about your proposals</h1>
              <p className="cp-empty-desc">
                I can analyse budgets, timelines, stakeholders, and more from your uploaded documents.
              </p>

              {/* Suggestion chips grid */}
              <div className="cp-chips" role="list" aria-label="Suggested questions">
                {SUGGESTIONS.map((s, i) => (
                  <button
                    key={i}
                    className="cp-chip"
                    onClick={() => pickSuggestion(s.text)}
                    type="button"
                    role="listitem"
                    aria-label={`Ask: ${s.text}`}
                    style={{ '--chip-delay': `${i * 0.06}s` }}
                  >
                    <span className="cp-chip-icon" aria-hidden="true">{s.icon}</span>
                    <span className="cp-chip-body">
                      <span className="cp-chip-label">{s.label}</span>
                      <span className="cp-chip-text">{s.text}</span>
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* ── MESSAGE LIST ── */}
          {messages.map((msg, i) => {
            const isUser = msg.role === 'user'
            const isAssistant = msg.role === 'assistant'
            return (
              <div
                key={i}
                className={`cp-msg cp-msg--${msg.role}`}
                aria-label={isUser ? 'Your message' : 'AI response'}
              >
                {/* AI avatar */}
                {isAssistant && (
                  <div className="cp-avatar cp-avatar--ai" aria-hidden="true">
                    <SparkleIcon />
                  </div>
                )}

                {/* Bubble + actions wrapper */}
                <div className="cp-bubble-wrap">
                  <div className="cp-bubble">
                    {/* Content */}
                    <p className="cp-bubble-text">{msg.content}</p>

                    {/* Timestamp */}
                    <time className="cp-bubble-time" dateTime={new Date().toISOString()} aria-label="Sent now">
                      {timeStr}
                    </time>
                  </div>

                  {/* Per-message action toolbar */}
                  <MessageActions
                    content={msg.content}
                    onRetry={isAssistant ? () => handleRetry(i) : undefined}
                  />
                </div>

                {/* User avatar */}
                {isUser && (
                  <div className="cp-avatar cp-avatar--user" aria-hidden="true">
                    <span>AS</span>
                  </div>
                )}
              </div>
            )
          })}

          {/* ── TYPING INDICATOR ── */}
          {isLoading && (
            <div className="cp-msg cp-msg--assistant" aria-label="AI is thinking" role="status">
              <div className="cp-avatar cp-avatar--ai" aria-hidden="true">
                <SparkleIcon />
              </div>
              <div className="cp-bubble-wrap">
                <div className="cp-bubble cp-bubble--typing">
                  <div className="cp-typing-dots" aria-hidden="true">
                    <span /><span /><span />
                  </div>
                  <span className="cp-typing-label">PitchCraft is thinking…</span>
                </div>
              </div>
            </div>
          )}

          {/* Scroll anchor */}
          <div ref={messagesEndRef} aria-hidden="true" />
        </div>
      </div>

      {/* ── SCROLL TO BOTTOM FAB ── */}
      <ScrollToBottomBtn visible={showScrollFab} onClick={scrollToBottom} />

      {/* ────────────────────────────────────────────────────────────────────
          INPUT AREA — pinned at bottom
      ─────────────────────────────────────────────────────────────────────*/}
      <div className="cp-input-outer" role="form" aria-label="Send a message">
        <div className="cp-input-inner">

          {/* Input shell with focus ring */}
          <div className={`cp-input-shell${focused ? ' cp-input-shell--focused' : ''}${isLoading ? ' cp-input-shell--loading' : ''}`}>

            {/* Attach button */}
            <button
              className="cp-tool-btn"
              title="Attach file"
              aria-label="Attach file"
              type="button"
              tabIndex={0}
            >
              <ClipIcon />
            </button>

            {/* Auto-growing textarea */}
            <textarea
              ref={textareaRef}
              id="cp-chat-input"
              className="cp-textarea"
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              placeholder="Ask about your proposals…"
              rows={1}
              disabled={isLoading}
              aria-label="Message input"
              aria-multiline="true"
              autoComplete="off"
              spellCheck="true"
            />

            {/* Right-side controls */}
            <div className="cp-input-tools">
              {/* Char count — shows when typing */}
              {charCount > 0 && (
                <span className="cp-char-count" aria-live="polite" aria-label={`${charCount} characters`}>
                  {charCount}
                </span>
              )}

              <div className="cp-input-divider" aria-hidden="true" />

              {/* Send button */}
              <button
                className={`cp-send-btn${isLoading ? ' cp-send-btn--loading' : ''}`}
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                type="button"
                aria-label="Send message"
                title="Send (Enter)"
              >
                {isLoading ? (
                  <span className="cp-send-spinner" aria-hidden="true" />
                ) : (
                  <SendIcon />
                )}
                <span>{isLoading ? 'Sending…' : 'Send'}</span>
              </button>
            </div>
          </div>

          {/* Keyboard hint */}
          <p className="cp-hint" aria-hidden="true">
            Press <kbd>Enter</kbd> to send · <kbd>Shift+Enter</kbd> for new line · <kbd>Esc</kbd> to dismiss
          </p>
        </div>
      </div>

    </div>
  )
}

export default ChatPage

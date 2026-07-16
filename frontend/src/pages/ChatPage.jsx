/* ============================================
   Chat Page — Real API Integration
   ============================================

   CONCEPT: Dynamic Rendering + Array.map()

   This page demonstrates the core chat UI pattern:
   1. Messages stored as an array in state
   2. Array.map() renders each message as a chat bubble
   3. New messages are appended to the array → React re-renders

   ADDITIONAL CONCEPTS:
   - useRef for auto-scrolling to latest message
   - onKeyDown for keyboard shortcuts (Enter to send)
   - Controlled input (value tied to state)
   - Immutable state updates (spread operator)
   ============================================ */

import { useRef, useEffect } from 'react'
import { sendChatMessage } from '../services/api'
import useChatStore from '../stores/useChatStore'
import './Pages.css'

function ChatPage() {
  const messages = useChatStore((s) => s.messages)
  const input = useChatStore((s) => s.input)
  const isLoading = useChatStore((s) => s.isLoading)
  const setInput = useChatStore((s) => s.setInput)
  const setIsLoading = useChatStore((s) => s.setIsLoading)
  const addMessage = useChatStore((s) => s.addMessage)

  /* REF: Reference to the messages container for auto-scroll */
  const messagesEndRef = useRef(null)

  /* REF: Reference to the textarea for auto-resize */
  const textareaRef = useRef(null)

  /* EFFECT: Auto-scroll to bottom when messages change.
     useEffect runs AFTER the component renders.
     This ensures we scroll after new messages appear in the DOM. */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])  // Re-run whenever messages array changes

  /* HELPER: Auto-resize textarea as user types */
  function handleInputChange(event) {
    setInput(event.target.value)

    // Auto-grow textarea (reset height, then set to scrollHeight)
    const textarea = event.target
    textarea.style.height = 'auto'
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px'
  }

  /* EVENT HANDLER: Send message on Enter (Shift+Enter for newline) */
  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()  // Prevent newline
      handleSend()
    }
  }

  /* API CALL: Send message to backend and get AI response */
  async function handleSend() {
    const { messages: currentMessages, isLoading: isBusy } = useChatStore.getState()
    const question = input.trim()
    if (!question || isBusy) return

    // Add user message to the list
    const userMessage = { role: 'user', content: question }
    addMessage(userMessage)

    setInput('')           // Clear the input
    setIsLoading(true)     // Show typing indicator

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }

    try {
      // Build conversation history for context
      const history = [...currentMessages, userMessage].map(msg => ({
        role: msg.role,
        content: msg.content
      }))

      const result = await sendChatMessage(question, history)

      // Add AI response to the list
      const assistantMessage = { role: 'assistant', content: result.answer }
      addMessage(assistantMessage)
    } catch (error) {
      // Add error as an assistant message
      const errorMessage = {
        role: 'assistant',
        content: `Sorry, something went wrong: ${error.message}`
      }
      addMessage(errorMessage)
    } finally {
      setIsLoading(false)
    }
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
        {/* MESSAGES AREA — scrollable list of chat bubbles */}
        <div className="chat-messages">
          {/* EMPTY STATE — shown when no messages yet */}
          {messages.length === 0 && (
            <div className="chat-empty">
              <div className="chat-empty-icon">💬</div>
              <h3>Ask anything about your proposals</h3>
              <p>e.g., "What's the budget for the AI project?"</p>
            </div>
          )}

          {/* RENDER LOOP: Array.map() converts each message object into JSX.
              React requires a unique "key" prop for each item in a list —
              it uses keys to efficiently update only changed items. */}
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

          {/* TYPING INDICATOR — shown while AI is generating */}
          {isLoading && (
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

          {/* Invisible anchor — we scroll to this */}
          <div ref={messagesEndRef} />
        </div>

        {/* INPUT AREA */}
        <div className="chat-input-area">
          <div className="chat-input-row">
            {/* Textarea — auto-grows as user types */}
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

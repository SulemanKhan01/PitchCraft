/* ============================================
   Chat Page — Placeholder
   ============================================

   CONCEPT: Component File Structure

   Every page component follows the same pattern:
   1. Import React hooks + CSS
   2. Define the component function
   3. Return JSX
   4. Export the component

   Later in Phase 5, this will become a full chat interface.
   ============================================ */

import './Pages.css'

function ChatPage() {
  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Chat with Proposals</h1>
        <p className="page-subtitle">
          Ask questions about your uploaded proposals and get AI-powered answers.
        </p>
      </div>

      <div className="placeholder-card">
        <div className="placeholder-card-icon">💬</div>
        <h3>Chat Interface Coming Soon</h3>
        <p>
          This is where you'll type questions and get responses
          from your proposal knowledge base, powered by Gemini AI.
        </p>
      </div>
    </div>
  )
}

export default ChatPage

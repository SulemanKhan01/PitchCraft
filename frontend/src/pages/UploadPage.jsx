/* ============================================
   Upload Page — Placeholder
   ============================================

   This will become the PDF upload interface in Phase 4.
   ============================================ */

import './Pages.css'

function UploadPage() {
  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Upload Proposals</h1>
        <p className="page-subtitle">
          Upload PDF proposals to build your knowledge base.
        </p>
      </div>

      <div className="placeholder-card">
        <div className="placeholder-card-icon">📄</div>
        <h3>Upload Interface Coming Soon</h3>
        <p>
          Drag and drop your PDF proposals here, or click to browse.
          They'll be indexed into the vector database for chat retrieval.
        </p>
      </div>
    </div>
  )
}

export default UploadPage

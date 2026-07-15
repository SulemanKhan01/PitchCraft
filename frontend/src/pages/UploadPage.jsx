/* ============================================
   Upload Page — Real API Integration
   ============================================

   CONCEPT: useState + Event Handling + API Calls

   This page demonstrates the core React pattern:
   1. User interacts with UI (clicks, drags, types)
   2. Event handler fires → calls setState
   3. State change → React re-renders → UI updates

   STATE VARIABLES:
   - selectedFile: The File object the user picked
   - isUploading: Whether an API call is in progress
   - status: { type: "success"|"error", message: "..." } — feedback to show

   EVENTS USED:
   - onClick: Click the dropzone to open file picker
   - onDragOver/onDragLeave/onDrop: Drag-and-drop file handling
   - onChange: When a file is selected via the hidden input
   ============================================ */

import { useState, useRef } from 'react'
import { uploadProposal } from '../api'
import './Pages.css'

function UploadPage() {
  /* STATE — React's way of remembering values across re-renders.
     When you call setX(), React re-renders the component with the new value. */
  const [selectedFile, setSelectedFile] = useState(null)
  const [isUploading, setIsUploading] = useState(false)
  const [status, setStatus] = useState(null)  // { type: "success"|"error", message: "..." }
  const [isDragOver, setIsDragOver] = useState(false)

  /* REF — A reference to a DOM element.
     useRef gives us access to the actual <input> element in the DOM.
     Unlike state, changing a ref does NOT cause a re-render.
     We use it to programmatically click the hidden file input. */
  const fileInputRef = useRef(null)

  /* EVENT HANDLER: User clicks the dropzone */
  function handleDropzoneClick() {
    fileInputRef.current.click()  // Programmatically click the hidden <input>
  }

  /* EVENT HANDLER: File is picked via the hidden input */
  function handleFileChange(event) {
    const file = event.target.files[0]  // event.target is the <input> element
    if (file) {
      setSelectedFile(file)
      setStatus(null)  // Clear any previous status
    }
  }

  /* EVENT HANDLER: File is dropped onto the zone */
  function handleDrop(event) {
    event.preventDefault()           // Prevent browser from opening the file
    setIsDragOver(false)
    const file = event.dataTransfer.files[0]
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file)
      setStatus(null)
    } else {
      setStatus({ type: 'error', message: 'Only PDF files are accepted.' })
    }
  }

  /* EVENT HANDLERS: Drag over/leave (for visual feedback) */
  function handleDragOver(event) {
    event.preventDefault()
    setIsDragOver(true)
  }

  function handleDragLeave() {
    setIsDragOver(false)
  }

  /* API CALL: Upload the selected file */
  async function handleUpload() {
    if (!selectedFile) return

    setIsUploading(true)
    setStatus(null)

    try {
      /* This calls our api.js function which uses fetch() under the hood.
         It sends a POST request with multipart/form-data containing the PDF. */
      const result = await uploadProposal(selectedFile)

      setStatus({
        type: 'success',
        message: `Uploaded "${selectedFile.name}" — categorized as "${result.category}" (${result.num_chunks} chunks indexed)`
      })
      setSelectedFile(null)  // Clear the selected file after success
    } catch (error) {
      setStatus({ type: 'error', message: error.message })
    } finally {
      setIsUploading(false)  // Always runs — whether success or error
    }
  }

  /* HELPER: Format file size (bytes → KB/MB) */
  function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / 1048576).toFixed(1) + ' MB'
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Upload Proposals</h1>
        <p className="page-subtitle">
          Upload PDF proposals to build your knowledge base for chat retrieval.
        </p>
      </div>

      {/* HIDDEN FILE INPUT — not visible, triggered programmatically */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf"
        className="upload-file-input"
        onChange={handleFileChange}
      />

      {/* DROP ZONE — click or drag files onto it */}
      <div
        className={`upload-dropzone${isDragOver ? ' dragover' : ''}`}
        onClick={handleDropzoneClick}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        <div className="upload-dropzone-icon">📄</div>
        <h3>Drop your PDF here</h3>
        <p>or <span className="browse-link">browse files</span> from your computer</p>
      </div>

      {/* SELECTED FILE — show info + upload button */}
      {selectedFile && (
        <div className="upload-file-info">
          <span className="upload-file-info-icon">📎</span>
          <div className="upload-file-info-details">
            <div className="upload-file-info-name">{selectedFile.name}</div>
            <div className="upload-file-info-size">{formatFileSize(selectedFile.size)}</div>
          </div>
          <button
            className="upload-file-info-remove"
            onClick={() => setSelectedFile(null)}
            disabled={isUploading}
          >
            ×
          </button>
        </div>
      )}

      {/* UPLOAD BUTTON */}
      {selectedFile && (
        <button
          className="upload-btn"
          onClick={handleUpload}
          disabled={isUploading}
        >
          {isUploading ? (
            <>
              <span className="spinner"></span>
              Uploading...
            </>
          ) : (
            'Upload Proposal'
          )}
        </button>
      )}

      {/* STATUS MESSAGE — success or error */}
      {status && (
        <div className={`upload-status ${status.type}`}>
          {status.type === 'success' ? '✓' : '✗'} {status.message}
        </div>
      )}
    </div>
  )
}

export default UploadPage

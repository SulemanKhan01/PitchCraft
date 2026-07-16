/* ============================================
   Cover Letter Page — Real API Integration
   ============================================

   CONCEPT: Blob Downloads + URL.createObjectURL()

   This page demonstrates:
   1. Text input → API call → Display generated content
   2. Binary file download (PDF) using Blob API

   THE DOWNLOAD PATTERN:
   1. fetch() returns a Response object
   2. response.blob() converts the response to a Blob (binary large object)
   3. URL.createObjectURL(blob) creates a temporary URL like "blob:http://..."
   4. Create a hidden <a> element, set its href to the blob URL
   5. Programmatically click it → browser downloads the file
   6. URL.revokeObjectURL(url) cleans up the temporary URL (frees memory)
   ============================================ */

import { generateCoverLetter, downloadCoverLetterPDF } from '../services/api'
import useCoverLetterStore from '../stores/useCoverLetterStore'
import './Pages.css'

function CoverLetterPage() {
  const jdText = useCoverLetterStore((s) => s.jdText)
  const generatedContent = useCoverLetterStore((s) => s.generatedContent)
  const isGenerating = useCoverLetterStore((s) => s.isGenerating)
  const isDownloading = useCoverLetterStore((s) => s.isDownloading)
  const chunksUsed = useCoverLetterStore((s) => s.chunksUsed)
  const error = useCoverLetterStore((s) => s.error)
  const setJdText = useCoverLetterStore((s) => s.setJdText)
  const setGeneratedContent = useCoverLetterStore((s) => s.setGeneratedContent)
  const setIsGenerating = useCoverLetterStore((s) => s.setIsGenerating)
  const setIsDownloading = useCoverLetterStore((s) => s.setIsDownloading)
  const setChunksUsed = useCoverLetterStore((s) => s.setChunksUsed)
  const setError = useCoverLetterStore((s) => s.setError)

  /* API CALL: Generate cover letter content from JD */
  async function handleGenerate() {
    if (!jdText.trim()) return

    setIsGenerating(true)
    setError(null)
    setGeneratedContent('')

    try {
      const result = await generateCoverLetter(jdText)
      setGeneratedContent(result.generated_content)
      setChunksUsed(result.num_chunks_used)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsGenerating(false)
    }
  }

  /* API CALL: Download the generated content as a styled PDF
     CONCEPT: Blob + ObjectURL + Programmatic download */
  async function handleDownloadPDF() {
    if (!generatedContent) return

    setIsDownloading(true)

    try {
      // Step 1: Fetch the PDF as binary data (Blob)
      const blob = await downloadCoverLetterPDF(generatedContent)

      // Step 2: Create a temporary URL pointing to this blob in memory
      const url = URL.createObjectURL(blob)

      // Step 3: Create a hidden <a> element
      const link = document.createElement('a')
      link.href = url
      link.download = 'cover-letter.pdf'  // Suggested filename

      // Step 4: Add to DOM, click it, remove it
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      // Step 5: Free the memory (the blob is now downloaded, no need for the URL)
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsDownloading(false)
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Cover Letter Generator</h1>
        <p className="page-subtitle">
          Paste a job description and get a tailored cover letter
          based on your past proposals.
        </p>
      </div>

      {/* JD INPUT */}
      <textarea
        className="cl-textarea"
        value={jdText}
        onChange={(e) => setJdText(e.target.value)}
        placeholder="Paste the job description here..."
        disabled={isGenerating}
      />

      {/* ACTION BUTTONS */}
      <div className="cl-actions">
        <button
          className="cl-btn cl-btn-primary"
          onClick={handleGenerate}
          disabled={!jdText.trim() || isGenerating}
        >
          {isGenerating ? (
            <>
              <span className="spinner"></span>
              Generating...
            </>
          ) : (
            '✨ Generate Cover Letter'
          )}
        </button>

        {generatedContent && (
          <button
            className="cl-btn cl-btn-secondary"
            onClick={handleDownloadPDF}
            disabled={isDownloading}
          >
            {isDownloading ? (
              <>
                <span className="spinner"></span>
                Downloading...
              </>
            ) : (
              '📥 Download PDF'
            )}
          </button>
        )}
      </div>

      {/* ERROR */}
      {error && (
        <div className="upload-status error" style={{ marginTop: '16px' }}>
          ✗ {error}
        </div>
      )}

      {/* GENERATED OUTPUT */}
      {generatedContent && (
        <div className="cl-output">
          <div className="cl-output-header">
            <h3>Generated Cover Letter</h3>
          </div>
          <div className="cl-output-text">{generatedContent}</div>
          <div className="cl-output-stats">
            Based on {chunksUsed} relevant proposal chunks
          </div>
        </div>
      )}
    </div>
  )
}

export default CoverLetterPage

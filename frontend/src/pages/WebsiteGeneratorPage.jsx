
import { useState } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { generateAndDeployWebsite } from '../services/api'
import './WebsiteGeneratorPage.css'

function WebsiteGeneratorPage() {
    const [jobDescription, setJobDescription] = useState('')
    const [customInstructions, setCustomInstructions] = useState('')
    const [isGenerating, setIsGenerating] = useState(false)
    const [result, setResult] = useState(null)
    const [error, setError] = useState(null)
    const [copied, setCopied] = useState(false)

    const { getToken } = useAuth()

    /* Handler: Trigger AI website generation & deployment */
    async function handleGenerate() {
        if (!jobDescription.trim() || isGenerating) return

        setIsGenerating(true)
        setError(null)
        setResult(null)
        setCopied(false)

        try {
            const token = await getToken()
            const res = await generateAndDeployWebsite(jobDescription, customInstructions, token)
            setResult(res)
        } catch (err) {
            setError(err.message || 'Failed to generate and deploy website')
        } finally {
            setIsGenerating(false)
        }
    }

    /* Handler: Copy live URL to clipboard */
    function handleCopyUrl() {
        if (!result?.public_url) return
        navigator.clipboard.writeText(result.public_url)
        setCopied(true)
        setTimeout(() => setCopied(false), 2500)
    }

    return (
        <div className="wg-page">

            {/* ── PAGE HEADER ── */}
            <div className="wg-header">
                <div className="wg-header-badge">
                    <span className="wg-header-badge-dot" />
                    AI-Powered Tool
                </div>
                <h1 className="wg-title">
                    Portfolio Demo{' '}
                    <span className="wg-title-accent">Website Generator</span>
                </h1>
                <p className="wg-subtitle">
                    Paste a client's job description to generate & deploy a relevant portfolio demo website to showcase as proof of work.
                </p>
            </div>

            {/* ── FORM CARD ── */}
            <div className="wg-form-card">

                {/* Job Description */}
                <div className="wg-field">
                    <label className="wg-label" htmlFor="wg-job-desc">
                        Client Job Description / Website Requirements
                        <span className="wg-label-required">*</span>
                    </label>
                    <textarea
                        id="wg-job-desc"
                        className="wg-textarea"
                        value={jobDescription}
                        onChange={(e) => setJobDescription(e.target.value)}
                        placeholder="e.g. Need a modern restaurant website with hero section, menu, testimonials, and contact form..."
                        disabled={isGenerating}
                        rows={7}
                    />
                </div>

                {/* Optional Instructions */}
                <div className="wg-field">
                    <label className="wg-label" htmlFor="wg-custom-instructions">
                        Additional Design Instructions
                        <span className="wg-label-optional">Optional</span>
                    </label>
                    <input
                        id="wg-custom-instructions"
                        type="text"
                        className="wg-input"
                        value={customInstructions}
                        onChange={(e) => setCustomInstructions(e.target.value)}
                        placeholder="e.g. Use a sleek dark mode theme with gold accents"
                        disabled={isGenerating}
                    />
                </div>

                {/* CTA Button */}
                <div className="wg-actions">
                    <button
                        id="wg-generate-btn"
                        className="wg-btn-primary"
                        onClick={handleGenerate}
                        disabled={!jobDescription.trim() || isGenerating}
                    >
                        {isGenerating ? (
                            <>
                                <span className="wg-spinner" />
                                Generating & Deploying…
                            </>
                        ) : (
                            <>
                                <span className="wg-btn-arrow">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M7 7h10v10" /><path d="M7 17 17 7" />
                                    </svg>
                                </span>
                                Generate & Deploy Demo Website
                            </>
                        )}
                    </button>
                </div>

                {/* Generating status */}
                {isGenerating && (
                    <div className="wg-generating-status">
                        <div className="wg-generating-dots">
                            <span /><span /><span />
                        </div>
                        Building your website with AI and deploying to Netlify…
                    </div>
                )}
            </div>

            {/* ── ERROR STATE ── */}
            {error && (
                <div className="wg-error" role="alert">
                    <svg className="wg-error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
                    </svg>
                    {error}
                </div>
            )}

            {/* ── SUCCESS RESULT CARD ── */}
            {result && (
                <div className="wg-result-card">

                    <div className="wg-result-header">
                        <div>
                            <div className="wg-result-title-row">
                                <div className="wg-result-success-badge">
                                    <span className="wg-result-success-dot" />
                                    Live
                                </div>
                                <h3 className="wg-result-site-title">
                                    {result.site_title || 'Demo Website Deployed'}
                                </h3>
                            </div>
                            <div className="wg-result-url-row">
                                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <circle cx="12" cy="12" r="10" /><line x1="2" y1="12" x2="22" y2="12" /><path d="M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z" />
                                </svg>
                                <a
                                    href={result.public_url}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="wg-result-url-link"
                                >
                                    {result.public_url}
                                </a>
                            </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="wg-result-actions">
                            <button
                                id="wg-copy-btn"
                                className="wg-btn-secondary"
                                onClick={handleCopyUrl}
                            >
                                {copied ? (
                                    <>
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                            <polyline points="20 6 9 17 4 12" />
                                        </svg>
                                        Copied!
                                    </>
                                ) : (
                                    <>
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <rect x="9" y="9" width="13" height="13" rx="2" /><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
                                        </svg>
                                        Copy Link
                                    </>
                                )}
                            </button>
                            <button
                                id="wg-open-btn"
                                className="wg-btn-open"
                                onClick={() => window.open(result.public_url, '_blank')}
                            >
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6" /><polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" />
                                </svg>
                                Open Live Site
                            </button>
                        </div>
                    </div>

                    {/* Live Preview iframe */}
                    <div className="wg-preview-section">
                        <div className="wg-preview-label">Live Preview</div>
                        <div className="wg-preview-frame-wrap">
                            <iframe
                                src={result.public_url}
                                title={result.site_title || 'Demo Website Preview'}
                                className="wg-preview-frame"
                            />
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default WebsiteGeneratorPage

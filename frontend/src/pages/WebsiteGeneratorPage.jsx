
import { useState } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { generateAndDeployWebsite } from '../services/api'
import './Pages.css'

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
        <div className="page" style={{ padding: '32px 40px', overflowY: 'auto' }}>
            {/* PAGE HEADER */}
            <div className="page-header">
                <h1 className="page-title">🌐 Portfolio Demo Website Generator</h1>
                <p className="page-subtitle">
                    Paste a client's job description to generate & deploy a relevant portfolio demo website to showcase as proof of work.
                </p>
            </div>

            {/* JOB DESCRIPTION INPUT */}
            <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: 'var(--text-heading)' }}>
                    Client Job Description / Website Requirements *
                </label>
                <textarea
                    className="cl-textarea"
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                    placeholder="e.g. Need a modern restaurant website with hero section, menu, testimonials, and contact form..."
                    disabled={isGenerating}
                    rows={6}
                />
            </div>

            {/* OPTIONAL CUSTOM INSTRUCTIONS */}
            <div style={{ marginBottom: '24px' }}>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: 'var(--text-heading)' }}>
                    Additional Design Instructions (Optional)
                </label>
                <input
                    type="text"
                    className="cl-textarea"
                    style={{ minHeight: '44px', height: '44px', padding: '10px 16px' }}
                    value={customInstructions}
                    onChange={(e) => setCustomInstructions(e.target.value)}
                    placeholder="e.g. Use a sleek dark mode theme with gold accents"
                    disabled={isGenerating}
                />
            </div>

            {/* ACTION BUTTON */}
            <div className="cl-actions">
                <button
                    className="cl-btn cl-btn-primary"
                    onClick={handleGenerate}
                    disabled={!jobDescription.trim() || isGenerating}
                >
                    {isGenerating ? (
                        <>
                            <span className="spinner"></span>
                            Generating & Deploying to Netlify...
                        </>
                    ) : (
                        '🚀 Generate & Deploy Demo Website'
                    )}
                </button>
            </div>

            {/* ERROR MESSAGE */}
            {error && (
                <div className="upload-status error" style={{ marginTop: '20px' }}>
                    ✗ {error}
                </div>
            )}

            {/* SUCCESS RESULT CARD + LIVE PREVIEW IFRAME */}
            {result && (
                <div className="cl-output" style={{ marginTop: '28px' }}>
                    <div className="cl-output-header">
                        <div>
                            <h3 style={{ fontSize: '1.2rem', margin: '0 0 4px 0', color: 'var(--text-heading)' }}>
                                🎉 {result.site_title || 'Demo Website Deployed'}
                            </h3>
                            <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--text-light)' }}>
                                Live URL:{' '}
                                <a
                                    href={result.public_url}
                                    target="_blank"
                                    rel="noreferrer"
                                    style={{ color: 'var(--primary)', fontWeight: '600', textDecoration: 'underline' }}
                                >
                                    {result.public_url}
                                </a>
                            </p>
                        </div>

                        {/* ACTION BUTTONS */}
                        <div style={{ display: 'flex', gap: '10px' }}>
                            <button className="cl-btn cl-btn-secondary" onClick={handleCopyUrl}>
                                {copied ? '✅ Copied!' : '📋 Copy Link'}
                            </button>
                            <button
                                className="cl-btn cl-btn-primary"
                                onClick={() => window.open(result.public_url, '_blank')}
                            >
                                🌐 Open Live Site ↗
                            </button>
                        </div>
                    </div>

                    {/* LIVE EMBEDDED IFRAME PREVIEW */}
                    <div style={{ marginTop: '20px' }}>
                        <h4 style={{ marginBottom: '10px', fontSize: '0.9375rem', color: 'var(--text-heading)' }}>
                            Live Website Preview:
                        </h4>
                        <iframe
                            src={result.public_url}
                            title={result.site_title || 'Demo Website Preview'}
                            style={{
                                width: '100%',
                                height: '520px',
                                borderRadius: '12px',
                                border: '1px solid var(--border)',
                                background: '#fff'
                            }}
                        />
                    </div>
                </div>
            )}
        </div>
    )
}

export default WebsiteGeneratorPage

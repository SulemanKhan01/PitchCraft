import { useState, useEffect, useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@clerk/clerk-react'
// import { listJobs, triggerJobScraper, updateJobStatus, deleteJob } from '../services/api'  // OLD
import { listJobs, triggerJobScraper, updateJobStatus, deleteJob, getScraperStatus, applyToJob } from '../services/api'  // NEW — added getScraperStatus, applyToJob
import './JobsPage.css'

export default function JobsPage() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [scraping, setScraping] = useState(false)
  const [notice, setNotice] = useState(null) // { type: 'info' | 'success' | 'error', text: '' }
  const [activeTab, setActiveTab] = useState('all') // 'all' | 'pending' | 'applied'
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedJobId, setExpandedJobId] = useState(null)

  // ── NEW: Auto-scraper timer state ──────────────────────────────────────────
  const [nextScrapeAt, setNextScrapeAt] = useState(null)   // ISO string from backend
  const [countdown, setCountdown] = useState(null)          // seconds remaining
  const [lastScrapedAt, setLastScrapedAt] = useState(null)  // ISO string

  const { getToken } = useAuth()
  const navigate = useNavigate()

  // ── Load Jobs ─────────────────────────────────────────────────────────────
  const loadJobsList = useCallback(async () => {
    try {
      setLoading(true)
      const token = await getToken()
      const data = await listJobs(token)
      setJobs(data || [])
    } catch (err) {
      console.error('Failed to load jobs:', err)
      setNotice({ type: 'error', text: err.message || 'Could not load jobs from database.' })
    } finally {
      setLoading(false)
    }
  }, [getToken])

  useEffect(() => {
    loadJobsList()
  }, [loadJobsList])

  // ── NEW: Poll scheduler status every 30s ──────────────────────────────────
  useEffect(() => {
    async function fetchStatus() {
      try {
        const status = await getScraperStatus()
        if (status.next_scrape_at) setNextScrapeAt(status.next_scrape_at)
        if (status.last_scraped_at) setLastScrapedAt(status.last_scraped_at)
      } catch (err) {
        console.warn('Could not fetch scraper status:', err)
      }
    }
    fetchStatus()
    const pollInterval = setInterval(fetchStatus, 30000) // re-poll every 30s
    return () => clearInterval(pollInterval)
  }, [])

  // ── NEW: Countdown ticker — ticks every second ────────────────────────────
  useEffect(() => {
    if (!nextScrapeAt) return
    function tick() {
      const diffSec = Math.max(0, Math.floor((new Date(nextScrapeAt) - new Date()) / 1000))
      setCountdown(diffSec)
      if (diffSec === 0) loadJobsList() // auto-refresh when timer hits 0
    }
    tick()
    const ticker = setInterval(tick, 1000)
    return () => clearInterval(ticker)
  }, [nextScrapeAt, loadJobsList])

  // ── Trigger Scraper ───────────────────────────────────────────────────────
  async function handleScrape() {
    try {
      setScraping(true)
      setNotice({
        type: 'info',
        text: '🚀 Scraper is running in the background... This takes about 30-60 seconds. Please wait!'
      })
      const token = await getToken()
      const res = await triggerJobScraper(token)
      
      setNotice({
        type: 'success',
        text: res.message || `Scraping finished! ${res.saved} new jobs saved.`
      })
      await loadJobsList()
    } catch (err) {
      console.error('Scraping error:', err)
      setNotice({
        type: 'error',
        text: err.message || 'Scraping failed. Make sure Upwork credentials are set in backend .env.'
      })
    } finally {
      setScraping(false)
    }
  }

  // ── Toggle Status ─────────────────────────────────────────────────────────
  async function handleToggleStatus(job) {
    const newStatus = job.status === 'applied' ? 'pending' : 'applied'
    // Optimistic UI update
    setJobs(prev => prev.map(j => j.id === job.id ? { ...j, status: newStatus } : j))

    try {
      const token = await getToken()
      await updateJobStatus(job.id, newStatus, token)
    } catch (err) {
      console.error('Failed to update status:', err)
      // Revert optimistic update on failure
      setJobs(prev => prev.map(j => j.id === job.id ? { ...j, status: job.status } : j))
      setNotice({ type: 'error', text: 'Failed to update job status.' })
    }
  }

  // ── Delete Job ────────────────────────────────────────────────────────────
  async function handleDeleteJob(jobId) {
    if (!window.confirm('Are you sure you want to remove this job?')) return
    setJobs(prev => prev.filter(j => j.id !== jobId))

    try {
      const token = await getToken()
      await deleteJob(jobId, token)
    } catch (err) {
      console.error('Failed to delete job:', err)
      await loadJobsList()
    }
  }

  // ── Navigate to Cover Letter ──────────────────────────────────────────────
  function handleGenerateCoverLetter(job) {
    // Pass job description to cover letter generator page
    navigate('/cover-letter', { state: { initialJdText: job.description } })
  }

  // ── Apply to Job (Phase 1) ────────────────────────────────────────────────
  async function handleApplyToJob(job) {
    try {
      setNotice({
        type: 'info',
        text: '🤖 Generating cover letter and opening browser to click Apply... This may take 30-60 seconds. Please wait!'
      })
      const token = await getToken()
      const res = await applyToJob(job.id, token)
      setNotice({
        type: 'success',
        text: `✅ ${res.message}`
      })
      await loadJobsList()
    } catch (err) {
      console.error('Apply error:', err)
      setNotice({
        type: 'error',
        text: err.message || 'Failed to apply to job.'
      })
    }
  }

  // ── Filtered Jobs ─────────────────────────────────────────────────────────
  const filteredJobs = useMemo(() => {
    return jobs.filter(job => {
      // Tab filter
      if (activeTab === 'pending' && job.status !== 'pending') return false
      if (activeTab === 'applied' && job.status !== 'applied') return false

      // Search filter
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase()
        const titleMatch = (job.title || '').toLowerCase().includes(query)
        const descMatch = (job.description || '').toLowerCase().includes(query)
        const skillsMatch = (job.skills || '').toLowerCase().includes(query)
        const categoryMatch = (job.category_name || '').toLowerCase().includes(query)
        return titleMatch || descMatch || skillsMatch || categoryMatch
      }

      return true
    })
  }, [jobs, activeTab, searchQuery])

  const pendingCount = jobs.filter(j => j.status === 'pending').length
  const appliedCount = jobs.filter(j => j.status === 'applied').length

  return (
    <div className="jobs-page">
      {/* Header */}
      <div className="jobs-page__header">
        <div className="jobs-page__title-area">
          <h1>
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
              <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
            </svg>
            Upwork Job Radar
          </h1>
          <p>Explore, filter, and track scraped Upwork opportunities in real-time.</p>
        </div>

        <div className="jobs-page__actions">

          {/* NEW: Auto-scrape countdown timer */}
          {countdown !== null && (
            <div className="jobs-page__timer">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
              </svg>
              <span>
                Next auto-scrape:{' '}
                <strong>
                  {String(Math.floor(countdown / 60)).padStart(2, '0')}:
                  {String(countdown % 60).padStart(2, '0')}
                </strong>
              </span>
            </div>
          )}

          <button
            className="jobs-page__scrape-btn"
            onClick={handleScrape}
            disabled={scraping}
            type="button"
          >
            {scraping ? (
              <>
                <span className="jobs-page__spinner" />
                Scraping Upwork...
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"></path>
                </svg>
                Scrape Jobs Now
              </>
            )}
          </button>
        </div>
      </div>

      {/* Notice Alert */}
      {notice && (
        <div className={`jobs-page__notice jobs-page__notice--${notice.type}`}>
          <span>{notice.text}</span>
        </div>
      )}

      {/* Toolbar */}
      <div className="jobs-page__toolbar">
        <div className="jobs-page__tabs">
          <button
            className={`jobs-page__tab ${activeTab === 'all' ? 'jobs-page__tab--active' : ''}`}
            onClick={() => setActiveTab('all')}
            type="button"
          >
            All Jobs <span className="jobs-page__tab-badge">{jobs.length}</span>
          </button>
          <button
            className={`jobs-page__tab ${activeTab === 'pending' ? 'jobs-page__tab--active' : ''}`}
            onClick={() => setActiveTab('pending')}
            type="button"
          >
            Pending <span className="jobs-page__tab-badge">{pendingCount}</span>
          </button>
          <button
            className={`jobs-page__tab ${activeTab === 'applied' ? 'jobs-page__tab--active' : ''}`}
            onClick={() => setActiveTab('applied')}
            type="button"
          >
            Applied <span className="jobs-page__tab-badge">{appliedCount}</span>
          </button>
        </div>

        <div className="jobs-page__search-wrap">
          <svg className="jobs-page__search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input
            type="text"
            className="jobs-page__search-input"
            placeholder="Filter by title, skill, category..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Jobs Container */}
      {loading ? (
        <div className="jobs-page__empty">
          <span className="jobs-page__spinner" style={{ width: 32, height: 32, margin: '0 auto 1rem' }} />
          <p>Loading scraped jobs from database...</p>
        </div>
      ) : filteredJobs.length === 0 ? (
        <div className="jobs-page__empty">
          <svg className="jobs-page__empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
          </svg>
          <h3>No jobs found</h3>
          <p>
            {jobs.length === 0
              ? 'Click "Scrape Jobs Now" to fetch live Upwork opportunities directly into your database.'
              : 'No jobs match your current search or tab filter.'}
          </p>
        </div>
      ) : (
        <div className="jobs-page__grid">
          {filteredJobs.map(job => {
            const isExpanded = expandedJobId === job.id
            const isApplied = job.status === 'applied'
            const skillsList = job.skills
              ? job.skills.replace(/[\[\]']/g, '').split(',').map(s => s.trim()).filter(Boolean)
              : []

            // Budget format
            let budgetText = ''
            if (job.fixed_budget_amount) budgetText = `$${job.fixed_budget_amount} (Fixed)`
            else if (job.hourly_min || job.hourly_max) budgetText = `$${job.hourly_min || 0} - $${job.hourly_max || 0}/hr`
            else if (job.type) budgetText = job.type

            return (
              <div key={job.id} className={`job-card job-card--${job.status}`}>
                {/* Header */}
                <div className="job-card__header">
                  <h2 className="job-card__title">
                    {job.url ? (
                      <a href={job.url} target="_blank" rel="noopener noreferrer">
                        {job.title}
                        <svg className="job-card__link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                          <polyline points="15 3 21 3 21 9"></polyline>
                          <line x1="10" y1="14" x2="21" y2="3"></line>
                        </svg>
                      </a>
                    ) : (
                      job.title
                    )}
                  </h2>

                  <button
                    className={`job-card__status-btn job-card__status-btn--${job.status}`}
                    onClick={() => handleToggleStatus(job)}
                    title="Click to toggle status"
                    type="button"
                  >
                    {isApplied ? (
                      <>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                          <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                        Applied
                      </>
                    ) : (
                      <>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <circle cx="12" cy="12" r="10"></circle>
                          <polyline points="12 6 12 12 16 14"></polyline>
                        </svg>
                        Pending
                      </>
                    )}
                  </button>
                </div>

                {/* Metadata Row */}
                <div className="job-card__meta">
                  {budgetText && <span className="job-badge job-badge--budget">{budgetText}</span>}
                  {job.category_name && <span className="job-badge">{job.category_name}</span>}
                  {job.level && <span className="job-badge job-badge--level">{job.level} level</span>}
                  {job.client_country && <span className="job-badge job-badge--country">📍 {job.client_country}</span>}
                  {job.client_rating && (
                    <span className="job-badge">⭐ {job.client_rating} ({job.client_reviews || 0})</span>
                  )}
                  {job.connects_required && (
                    <span className="job-badge">⚡ {job.connects_required} Connects</span>
                  )}
                </div>

                {/* Description */}
                <div className={`job-card__desc ${!isExpanded ? 'job-card__desc--truncated' : ''}`}>
                  {job.description || 'No description provided.'}
                </div>

                {job.description && job.description.length > 220 && (
                  <button
                    className="job-card__read-more"
                    onClick={() => setExpandedJobId(isExpanded ? null : job.id)}
                    type="button"
                  >
                    {isExpanded ? 'Show less ▲' : 'Read full description ▼'}
                  </button>
                )}

                {/* Skills */}
                {skillsList.length > 0 && (
                  <div className="job-card__skills">
                    {skillsList.slice(0, 10).map((skill, idx) => (
                      <span key={idx} className="job-skill-tag">{skill}</span>
                    ))}
                  </div>
                )}

                {/* Footer */}
                <div className="job-card__footer">
                  <span className="job-card__date">
                    Scraped {new Date(job.scraped_at).toLocaleDateString()}
                  </span>

                  <div className="job-card__actions">
                    <button
                      className="job-card__pitch-btn"
                      onClick={() => handleGenerateCoverLetter(job)}
                      title="Generate AI cover letter for this job"
                      type="button"
                    >
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M12 20h9"></path>
                        <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
                      </svg>
                      Generate Proposal
                    </button>

                    <button
                      className="job-card__apply-btn"
                      onClick={() => handleApplyToJob(job)}
                      title="Generate cover letter and click Apply on Upwork"
                      type="button"
                      disabled={job.status === 'applied'}
                    >
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="9 11 12 14 22 4"></polyline>
                        <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
                      </svg>
                      {job.status === 'applied' ? 'Applied' : 'Apply'}
                    </button>

                    <button
                      className="job-card__delete-btn"
                      onClick={() => handleDeleteJob(job.id)}
                      title="Delete job"
                      type="button"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

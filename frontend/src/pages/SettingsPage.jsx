/**
 * SettingsPage.jsx — PitchCraft Settings
 *
 * Sections:
 *  1. AI & RAG Engine Settings
 *  2. Proposal & Cover Letter Defaults
 *  3. API Keys & Integrations
 *  4. Account & Profile
 *  5. Appearance & Interface
 */

import { useState } from 'react'
import { useUser, useClerk } from '@clerk/clerk-react'
import useSettingsStore from '../stores/useSettingsStore'
import './SettingsPage.css'

/* ── Icon helpers ─────────────────────────────────────────────────────────── */
const Icon = ({ d, size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"
    aria-hidden="true">
    <path d={d} />
  </svg>
)

/* ── Toast notification ───────────────────────────────────────────────────── */
function Toast({ message, type }) {
  return (
    <div className={`sp-toast sp-toast--${type}`}>
      {type === 'success'
        ? <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
        : <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg>
      }
      {message}
    </div>
  )
}

/* ── Section wrapper ──────────────────────────────────────────────────────── */
function Section({ id, icon, title, subtitle, children }) {
  return (
    <section className="sp-section" id={id}>
      <div className="sp-section__head">
        <div className="sp-section__icon">{icon}</div>
        <div>
          <h2 className="sp-section__title">{title}</h2>
          {subtitle && <p className="sp-section__subtitle">{subtitle}</p>}
        </div>
      </div>
      <div className="sp-section__body">{children}</div>
    </section>
  )
}

/* ── Field row ────────────────────────────────────────────────────────────── */
function FieldRow({ label, hint, children }) {
  return (
    <div className="sp-field">
      <div className="sp-field__label-group">
        <span className="sp-field__label">{label}</span>
        {hint && <span className="sp-field__hint">{hint}</span>}
      </div>
      <div className="sp-field__control">{children}</div>
    </div>
  )
}

/* ── Toggle switch ────────────────────────────────────────────────────────── */
function Toggle({ id, checked, onChange }) {
  return (
    <label className="sp-toggle" htmlFor={id}>
      <input id={id} type="checkbox" checked={checked} onChange={onChange} className="sp-toggle__input" />
      <span className="sp-toggle__track">
        <span className="sp-toggle__thumb" />
      </span>
    </label>
  )
}

/* ── Slider ───────────────────────────────────────────────────────────────── */
function Slider({ id, min, max, step, value, onChange, format }) {
  const pct = ((value - min) / (max - min)) * 100
  return (
    <div className="sp-slider-wrap">
      <input
        id={id} type="range" min={min} max={max} step={step} value={value}
        onChange={onChange} className="sp-slider"
        style={{ '--pct': `${pct}%` }}
      />
      <span className="sp-slider__value">{format ? format(value) : value}</span>
    </div>
  )
}

/* ── Select ───────────────────────────────────────────────────────────────── */
function Select({ id, value, onChange, options }) {
  return (
    <div className="sp-select-wrap">
      <select id={id} value={value} onChange={onChange} className="sp-select">
        {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
      <svg className="sp-select__arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9" /></svg>
    </div>
  )
}

/* ── Input ────────────────────────────────────────────────────────────────── */
function TextInput({ id, value, onChange, placeholder, type = 'text' }) {
  return (
    <input
      id={id} type={type} value={value} onChange={onChange}
      placeholder={placeholder} className="sp-input"
    />
  )
}

/* ── Password Input ───────────────────────────────────────────────────────── */
function PasswordInput({ id, value, onChange, placeholder }) {
  const [show, setShow] = useState(false)
  return (
    <div className="sp-input-wrap">
      <input
        id={id} type={show ? 'text' : 'password'} value={value}
        onChange={onChange} placeholder={placeholder} className="sp-input sp-input--pw"
      />
      <button type="button" className="sp-pw-toggle" onClick={() => setShow(s => !s)} aria-label="Toggle visibility">
        {show
          ? <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94" /><path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19" /><line x1="1" y1="1" x2="23" y2="23" /></svg>
          : <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" /></svg>
        }
      </button>
    </div>
  )
}

/* ═══════════════════════════════════════════════════════════════════════════
   MAIN SETTINGS PAGE
═══════════════════════════════════════════════════════════════════════════ */
function SettingsPage() {
  const { user } = useUser()
  const { openUserProfile } = useClerk()
  const settings = useSettingsStore()
  const update = useSettingsStore(s => s.updateSettings)
  const reset = useSettingsStore(s => s.resetSettings)

  const [toast, setToast] = useState(null)
  const [activeSection, setActiveSection] = useState('ai')

  function showToast(message, type = 'success') {
    setToast({ message, type })
    setTimeout(() => setToast(null), 3000)
  }

  function handleSave() {
    // Settings auto-persist via Zustand persist middleware
    showToast('Settings saved successfully!')
  }

  function handleReset() {
    reset()
    showToast('Settings reset to defaults.', 'info')
  }

  const userEmail = user?.primaryEmailAddress?.emailAddress || ''
  const initials = userEmail ? userEmail.slice(0, 2).toUpperCase() : 'PC'

  const navItems = [
    { id: 'ai',       label: 'AI Engine',      icon: 'M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5' },
    { id: 'proposal', label: 'Proposal Output', icon: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8' },
    { id: 'apikeys',  label: 'API Keys',        icon: 'M21 2l-2 2m-7.61 7.61a5.5 5.5 0 11-7.778 7.778 5.5 5.5 0 017.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4' },
    { id: 'account',  label: 'Account',         icon: 'M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 3a4 4 0 100 8 4 4 0 000-8z' },
    { id: 'appear',   label: 'Appearance',      icon: 'M12 22C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10-4.477 10-10 10zm-4-9a4 4 0 108 0' },
  ]

  return (
    <div className="sp-root">
      {/* Ambient glows */}
      <div className="sp-glow sp-glow--1" />
      <div className="sp-glow sp-glow--2" />

      {/* Toast */}
      {toast && <Toast message={toast.message} type={toast.type} />}

      {/* Page header */}
      <header className="sp-header">
        <div className="sp-header__left">
          <div className="sp-header__icon-wrap">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.07 4.93a10 10 0 010 14.14M4.93 4.93a10 10 0 000 14.14" />
            </svg>
          </div>
          <div>
            <h1 className="sp-header__title">Settings</h1>
            <p className="sp-header__sub">Customize your PitchCraft AI experience</p>
          </div>
        </div>
        <div className="sp-header__actions">
          <button className="sp-btn sp-btn--ghost" onClick={handleReset} type="button">
            Reset Defaults
          </button>
          <button className="sp-btn sp-btn--primary" onClick={handleSave} type="button">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z" />
              <polyline points="17 21 17 13 7 13 7 21" />
              <polyline points="7 3 7 8 15 8" />
            </svg>
            Save Settings
          </button>
        </div>
      </header>

      <div className="sp-layout">
        {/* Sidebar nav */}
        <nav className="sp-nav">
          {navItems.map(item => (
            <button
              key={item.id}
              className={`sp-nav__item${activeSection === item.id ? ' sp-nav__item--active' : ''}`}
              onClick={() => setActiveSection(item.id)}
              type="button"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                <path d={item.icon} />
              </svg>
              {item.label}
            </button>
          ))}
        </nav>

        {/* Main content area */}
        <main className="sp-content">

          {/* ─── AI Engine ─────────────────────────────────────────── */}
          {activeSection === 'ai' && (
            <Section
              id="ai"
              title="AI & RAG Engine"
              subtitle="Control how the AI retrieves and generates answers."
              icon={
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                </svg>
              }
            >
              <FieldRow label="Default AI Model" hint="Used for answer generation across all pipelines">
                <Select
                  id="ai-model"
                  value={settings.aiModel}
                  onChange={e => update({ aiModel: e.target.value })}
                  options={[
                    { value: 'gemini-3.1-flash-lite', label: 'Gemini 3.1 Flash Lite (Fast)' },
                    { value: 'gemini-3.1-flash',      label: 'Gemini 3.1 Flash (Balanced)' },
                    { value: 'gemini-3.1-pro',        label: 'Gemini 3.1 Pro (Powerful)' },
                  ]}
                />
              </FieldRow>

              <FieldRow
                label="Retrieval Score Threshold"
                hint={`Only chunks scoring ≥ ${settings.scoreThreshold.toFixed(2)} are used. Lower = more results, higher = more precise.`}
              >
                <Slider
                  id="score-threshold"
                  min={0.30} max={0.90} step={0.01}
                  value={settings.scoreThreshold}
                  onChange={e => update({ scoreThreshold: parseFloat(e.target.value) })}
                  format={v => v.toFixed(2)}
                />
              </FieldRow>

              <FieldRow
                label="Max Context Chunks"
                hint="Number of document chunks passed to the LLM per query."
              >
                <Slider
                  id="max-chunks"
                  min={2} max={12} step={1}
                  value={settings.maxChunks}
                  onChange={e => update({ maxChunks: parseInt(e.target.value) })}
                />
              </FieldRow>

              <FieldRow
                label="Web Search Fallback"
                hint="Automatically search the web via Tavily when no relevant documents are found."
              >
                <Toggle
                  id="web-search"
                  checked={settings.webSearchEnabled}
                  onChange={e => update({ webSearchEnabled: e.target.checked })}
                />
              </FieldRow>

              <div className="sp-info-card">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                <span>The current active pipeline uses <strong>LangGraph</strong> with conditional routing: vector DB → (fallback) → web search → Gemini generation.</span>
              </div>
            </Section>
          )}

          {/* ─── Proposal & Cover Letter ────────────────────────────── */}
          {activeSection === 'proposal' && (
            <Section
              id="proposal"
              title="Proposal & Cover Letter Defaults"
              subtitle="Customize the default output style and profile information."
              icon={
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                  <polyline points="10 9 9 9 8 9" />
                </svg>
              }
            >
              <FieldRow label="Writing Tone & Style" hint="Default tone applied to proposal and cover letter generation.">
                <Select
                  id="writing-tone"
                  value={settings.writingTone}
                  onChange={e => update({ writingTone: e.target.value })}
                  options={[
                    { value: 'enterprise',  label: 'Enterprise & Corporate' },
                    { value: 'persuasive',  label: 'Modern & Persuasive' },
                    { value: 'technical',   label: 'Technical & Detailed' },
                    { value: 'direct',      label: 'Direct & Concise' },
                    { value: 'friendly',    label: 'Warm & Friendly' },
                  ]}
                />
              </FieldRow>

              <FieldRow label="Agency / Freelancer Name" hint="Injected into generated proposals and cover letters.">
                <TextInput
                  id="agency-name"
                  value={settings.agencyName}
                  onChange={e => update({ agencyName: e.target.value })}
                  placeholder="e.g. Acme Software Solutions"
                />
              </FieldRow>

              <FieldRow label="Portfolio / Website URL" hint="Referenced in the 'Why Choose Us' section of proposals.">
                <TextInput
                  id="portfolio-url"
                  value={settings.portfolioUrl}
                  onChange={e => update({ portfolioUrl: e.target.value })}
                  placeholder="https://yourportfolio.com"
                />
              </FieldRow>

              <FieldRow label="Standard Signature / Sign-off" hint="Appended to the closing of generated cover letters.">
                <textarea
                  id="signature-text"
                  value={settings.signatureText}
                  onChange={e => update({ signatureText: e.target.value })}
                  placeholder="e.g. Best regards,&#10;John Doe&#10;Lead Engineer"
                  className="sp-textarea"
                  rows={3}
                />
              </FieldRow>

              <FieldRow label="PDF Export Template" hint="Visual layout applied when downloading generated cover letters as PDF.">
                <div className="sp-template-grid">
                  {[
                    { value: 'minimalist', label: 'Minimalist', desc: 'Clean, white space' },
                    { value: 'modern',     label: 'Modern',     desc: 'Purple accents' },
                    { value: 'corporate',  label: 'Corporate',  desc: 'Formal & structured' },
                  ].map(t => (
                    <button
                      key={t.value}
                      type="button"
                      className={`sp-template-card${settings.pdfTemplate === t.value ? ' sp-template-card--active' : ''}`}
                      onClick={() => update({ pdfTemplate: t.value })}
                    >
                      <div className="sp-template-card__preview">
                        <div className="sp-template-card__line sp-template-card__line--h" />
                        <div className="sp-template-card__line" />
                        <div className="sp-template-card__line" />
                        <div className="sp-template-card__line sp-template-card__line--short" />
                      </div>
                      <span className="sp-template-card__name">{t.label}</span>
                      <span className="sp-template-card__desc">{t.desc}</span>
                      {settings.pdfTemplate === t.value && (
                        <div className="sp-template-card__check">
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                            <polyline points="20 6 9 17 4 12" />
                          </svg>
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              </FieldRow>
            </Section>
          )}

          {/* ─── API Keys ───────────────────────────────────────────── */}
          {activeSection === 'apikeys' && (
            <Section
              id="apikeys"
              title="API Keys & Integrations"
              subtitle="Manage third-party service keys and check connection health."
              icon={
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 11-7.778 7.778 5.5 5.5 0 017.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4" />
                </svg>
              }
            >
              <FieldRow label="Tavily Web Search API Key" hint="Required for web search fallback. Get yours at tavily.com">
                <PasswordInput
                  id="tavily-key"
                  value={settings.tavilyApiKey}
                  onChange={e => update({ tavilyApiKey: e.target.value })}
                  placeholder="tvly-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                />
              </FieldRow>

              <div className="sp-divider" />

              <div className="sp-integration-list">
                <div className="sp-integration">
                  <div className="sp-integration__left">
                    <div className="sp-integration__icon sp-integration__icon--gemini">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                      </svg>
                    </div>
                    <div>
                      <div className="sp-integration__name">Google Gemini AI</div>
                      <div className="sp-integration__desc">LLM for answer generation &amp; analysis</div>
                    </div>
                  </div>
                  <div className="sp-badge sp-badge--active">
                    <span className="sp-badge__dot" />
                    Connected
                  </div>
                </div>

                <div className="sp-integration">
                  <div className="sp-integration__left">
                    <div className="sp-integration__icon sp-integration__icon--qdrant">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                        <ellipse cx="12" cy="5" rx="9" ry="3" />
                        <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
                        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
                      </svg>
                    </div>
                    <div>
                      <div className="sp-integration__name">Qdrant Vector DB</div>
                      <div className="sp-integration__desc">Semantic search &amp; proposal indexing</div>
                    </div>
                  </div>
                  <div className="sp-badge sp-badge--active">
                    <span className="sp-badge__dot" />
                    Connected
                  </div>
                </div>

                <div className="sp-integration">
                  <div className="sp-integration__left">
                    <div className="sp-integration__icon sp-integration__icon--tavily">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
                      </svg>
                    </div>
                    <div>
                      <div className="sp-integration__name">Tavily Web Search</div>
                      <div className="sp-integration__desc">Web fallback for unanswered queries</div>
                    </div>
                  </div>
                  <div className={`sp-badge ${settings.tavilyApiKey ? 'sp-badge--active' : 'sp-badge--warn'}`}>
                    <span className="sp-badge__dot" />
                    {settings.tavilyApiKey ? 'Configured' : 'Key Missing'}
                  </div>
                </div>

                <div className="sp-integration">
                  <div className="sp-integration__left">
                    <div className="sp-integration__icon sp-integration__icon--clerk">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                        <path d="M7 11V7a5 5 0 0110 0v4" />
                      </svg>
                    </div>
                    <div>
                      <div className="sp-integration__name">Clerk Authentication</div>
                      <div className="sp-integration__desc">Secure user auth &amp; session management</div>
                    </div>
                  </div>
                  <div className="sp-badge sp-badge--active">
                    <span className="sp-badge__dot" />
                    Active
                  </div>
                </div>
              </div>
            </Section>
          )}

          {/* ─── Account ────────────────────────────────────────────── */}
          {activeSection === 'account' && (
            <Section
              id="account"
              title="Account & Profile"
              subtitle="Manage your account details and security settings."
              icon={
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
              }
            >
              {/* Account card */}
              <div className="sp-account-card">
                <div className="sp-account-card__avatar">{initials}</div>
                <div className="sp-account-card__info">
                  <div className="sp-account-card__name">{userEmail.split('@')[0] || 'User'}</div>
                  <div className="sp-account-card__email">{userEmail || 'No email'}</div>
                  <div className="sp-account-card__plan">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                    </svg>
                    Pro Plan — Gemini Powered
                  </div>
                </div>
              </div>

              <div className="sp-account-actions">
                <button
                  className="sp-account-action-btn"
                  type="button"
                  onClick={() => openUserProfile()}
                >
                  <div className="sp-account-action-btn__icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
                      <circle cx="12" cy="7" r="4" />
                    </svg>
                  </div>
                  <div className="sp-account-action-btn__text">
                    <span className="sp-account-action-btn__label">Manage Profile</span>
                    <span className="sp-account-action-btn__sub">Update name, avatar &amp; email</span>
                  </div>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="sp-account-action-btn__arrow">
                    <path d="M9 18l6-6-6-6" />
                  </svg>
                </button>

                <button
                  className="sp-account-action-btn"
                  type="button"
                  onClick={() => openUserProfile({ initialPage: 'security' })}
                >
                  <div className="sp-account-action-btn__icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                      <path d="M7 11V7a5 5 0 0110 0v4" />
                    </svg>
                  </div>
                  <div className="sp-account-action-btn__text">
                    <span className="sp-account-action-btn__label">Security &amp; Password</span>
                    <span className="sp-account-action-btn__sub">Change password, enable 2FA / MFA</span>
                  </div>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="sp-account-action-btn__arrow">
                    <path d="M9 18l6-6-6-6" />
                  </svg>
                </button>

                <button
                  className="sp-account-action-btn"
                  type="button"
                  onClick={() => openUserProfile({ initialPage: 'connected-accounts' })}
                >
                  <div className="sp-account-action-btn__icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71" />
                      <path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71" />
                    </svg>
                  </div>
                  <div className="sp-account-action-btn__text">
                    <span className="sp-account-action-btn__label">Connected Accounts</span>
                    <span className="sp-account-action-btn__sub">Google, GitHub, and more</span>
                  </div>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="sp-account-action-btn__arrow">
                    <path d="M9 18l6-6-6-6" />
                  </svg>
                </button>
              </div>
            </Section>
          )}

          {/* ─── Appearance ─────────────────────────────────────────── */}
          {activeSection === 'appear' && (
            <Section
              id="appear"
              title="Appearance & Interface"
              subtitle="Adjust the look and behaviour of your PitchCraft workspace."
              icon={
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 22C6.477 22 2 17.523 2 12S6.477 2 12 2" />
                </svg>
              }
            >
              <FieldRow label="Theme" hint="Interface colour scheme. Dark mode uses glassmorphism styling.">
                <div className="sp-theme-grid">
                  {[
                    { value: 'dark',   label: 'Dark',   sub: 'Glassmorphism' },
                    { value: 'system', label: 'System', sub: 'Follows OS'    },
                  ].map(t => (
                    <button
                      key={t.value}
                      type="button"
                      className={`sp-theme-btn${settings.theme === t.value ? ' sp-theme-btn--active' : ''}`}
                      onClick={() => update({ theme: t.value })}
                    >
                      <span className="sp-theme-btn__icon">
                        {t.value === 'dark'
                          ? <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" /></svg>
                          : <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5" /><line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" /><line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" /><line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" /></svg>
                        }
                      </span>
                      <span className="sp-theme-btn__label">{t.label}</span>
                      <span className="sp-theme-btn__sub">{t.sub}</span>
                      {settings.theme === t.value && (
                        <span className="sp-theme-btn__check">
                          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                            <polyline points="20 6 9 17 4 12" />
                          </svg>
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              </FieldRow>


              <FieldRow
                label="Debug / Developer Mode"
                hint="Show Query Betterment breakdown (spell check, intent, expansion) below each chat response."
              >
                <Toggle
                  id="debug-mode"
                  checked={settings.debugMode}
                  onChange={e => update({ debugMode: e.target.checked })}
                />
              </FieldRow>

              <FieldRow
                label="Auto-Scroll to Latest Message"
                hint="Automatically scroll to the newest message during chat streaming."
              >
                <Toggle
                  id="auto-scroll"
                  checked={settings.autoScroll}
                  onChange={e => update({ autoScroll: e.target.checked })}
                />
              </FieldRow>

              <div className="sp-info-card">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                <span>Light mode support and additional theme customisation is coming in a future release.</span>
              </div>
            </Section>
          )}

        </main>
      </div>
    </div>
  )
}

export default SettingsPage

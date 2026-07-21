/**
 * AuthLayout.jsx
 * ─────────────────────────────────────────────────────────────────────────────
 * Shared visual shell for Login & Sign-up pages.
 * Wraps Clerk's <SignIn /> / <SignUp /> components with:
 *   • Animated mesh-gradient background (21st-inspired pattern: id 18017, 18273)
 *   • Floating neon orbs (21st-inspired: id 18486, 9544)
 *   • Subtle animated grid overlay
 *   • Left branding panel (desktop) with staggered entrance
 *   • Right glassmorphism card panel containing the Clerk form
 *   • Smooth fade-in on mount; respects prefers-reduced-motion
 *
 * Props:
 *   mode   : 'login' | 'register' — determines headline copy
 *   children: the Clerk <SignIn /> or <SignUp /> node
 * ─────────────────────────────────────────────────────────────────────────────
 */

import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import './AuthLayout.css'

/* ── SVG brand mark ──────────────────────────────────────────────────────── */
const BrandMark = () => (
  <svg viewBox="0 0 40 40" fill="none" aria-hidden="true" className="al-brand-svg">
    <defs>
      <linearGradient id="bm-grad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
        <stop offset="0%" stopColor="#7c3aed"/>
        <stop offset="100%" stopColor="#c026d3"/>
      </linearGradient>
    </defs>
    <rect width="40" height="40" rx="11" fill="url(#bm-grad)"/>
    <path d="M12 28L20 10l8 18" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M14.5 22.5h11" stroke="#fff" strokeWidth="2" strokeLinecap="round" opacity=".7"/>
  </svg>
)

/* ── Feature list items shown on the branding panel ─────────────────────── */
const FEATURES = [
  { icon: '📄', text: 'AI-powered proposal analysis' },
  { icon: '💬', text: 'Intelligent Q&A on your documents' },
  { icon: '✉️',  text: 'Auto-generated cover letters' },
  { icon: '🔒', text: 'Enterprise-grade security via Clerk' },
]

/* ── Animated canvas background (mesh gradient + moving orbs) ───────────── */
function AnimatedBackground() {
  const canvasRef = useRef(null)

  useEffect(() => {
    /* Respect prefers-reduced-motion */
    const motionOK = !window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (!motionOK) return

    const canvas  = canvasRef.current
    const ctx     = canvas.getContext('2d')
    let   rafId   = null
    let   t       = 0

    /* Orb definitions — inspired by 21st.dev Gradient Orb (id: 18486) */
    const orbs = [
      { x: 0.15, y: 0.2,  r: 0.38, color: 'rgba(124,58,237,0.18)',  dx: 0.00012, dy: 0.00007 },
      { x: 0.72, y: 0.65, r: 0.32, color: 'rgba(192,38,211,0.14)',  dx:-0.00009, dy: 0.00011 },
      { x: 0.5,  y: 0.9,  r: 0.22, color: 'rgba(139,92,246,0.12)',  dx: 0.00008, dy:-0.00013 },
      { x: 0.85, y: 0.12, r: 0.18, color: 'rgba(99,102,241,0.1)',   dx:-0.00011, dy: 0.00009 },
    ]

    function resize() {
      canvas.width  = window.innerWidth
      canvas.height = window.innerHeight
    }
    resize()
    window.addEventListener('resize', resize)

    function draw() {
      const W = canvas.width
      const H = canvas.height
      ctx.clearRect(0, 0, W, H)

      /* Base deep-dark fill */
      ctx.fillStyle = '#0b0914'
      ctx.fillRect(0, 0, W, H)

      /* Draw orbs with radial gradients */
      orbs.forEach(o => {
        const cx = o.x * W
        const cy = o.y * H
        const r  = o.r * Math.min(W, H)
        const g  = ctx.createRadialGradient(cx, cy, 0, cx, cy, r)
        g.addColorStop(0, o.color)
        g.addColorStop(1, 'transparent')
        ctx.fillStyle = g
        ctx.beginPath()
        ctx.arc(cx, cy, r, 0, Math.PI * 2)
        ctx.fill()

        /* Drift orbs slowly */
        o.x += o.dx
        o.y += o.dy
        if (o.x < -0.2 || o.x > 1.2) o.dx *= -1
        if (o.y < -0.2 || o.y > 1.2) o.dy *= -1
      })

      /* Subtle dot-grid overlay (21st mesh pattern inspiration) */
      const spacing = 36
      ctx.fillStyle = 'rgba(255,255,255,0.025)'
      for (let x = 0; x < W; x += spacing) {
        for (let y = 0; y < H; y += spacing) {
          const pulse = Math.sin(t * 0.0008 + x * 0.01 + y * 0.01) * 0.4 + 0.6
          ctx.globalAlpha = 0.03 * pulse
          ctx.beginPath()
          ctx.arc(x, y, 1.2, 0, Math.PI * 2)
          ctx.fill()
        }
      }
      ctx.globalAlpha = 1

      t++
      rafId = requestAnimationFrame(draw)
    }

    rafId = requestAnimationFrame(draw)
    return () => {
      cancelAnimationFrame(rafId)
      window.removeEventListener('resize', resize)
    }
  }, [])

  return <canvas ref={canvasRef} className="al-canvas" aria-hidden="true"/>
}

/* ── Main layout component ───────────────────────────────────────────────── */
export default function AuthLayout({ mode = 'login', children }) {
  const isLogin = mode === 'login'

  return (
    <div className="al-root" role="main">

      {/* Animated canvas background */}
      <AnimatedBackground />

      {/* ── Floating decorative orbs (CSS-animated, layered over canvas) ── */}
      <div className="al-orb al-orb--1" aria-hidden="true"/>
      <div className="al-orb al-orb--2" aria-hidden="true"/>
      <div className="al-orb al-orb--3" aria-hidden="true"/>

      {/* ── Main two-column card ── */}
      <div className="al-card" role="dialog" aria-label={isLogin ? 'Sign in to PitchCraft' : 'Create your PitchCraft account'}>

        {/* ────────────────────────────────────────────────────────────────
            LEFT — Branding Panel (hidden on mobile)
        ──────────────────────────────────────────────────────────────── */}
        <div className="al-brand-panel" aria-hidden="true">

          {/* Logo + wordmark */}
          <div className="al-brand-logo">
            <BrandMark />
            <span className="al-brand-name">PitchCraft</span>
          </div>

          {/* Animated tagline */}
          <div className="al-brand-copy">
            <h1 className="al-brand-headline">
              Win more deals<br/>
              <span className="al-brand-accent">with AI precision.</span>
            </h1>
            <p className="al-brand-sub">
              Analyze proposals, generate cover letters, and chat with your
              documents — all in one intelligent workspace.
            </p>
          </div>

          {/* Feature list */}
          <ul className="al-features" aria-label="PitchCraft features">
            {FEATURES.map((f, i) => (
              <li key={i} className="al-feature-item" style={{ '--fi': i }}>
                <span className="al-feature-icon" role="img" aria-hidden="true">{f.icon}</span>
                <span>{f.text}</span>
              </li>
            ))}
          </ul>

          {/* Decorative inner glow */}
          <div className="al-brand-glow" aria-hidden="true"/>
        </div>

        {/* ────────────────────────────────────────────────────────────────
            RIGHT — Clerk Form Panel
        ──────────────────────────────────────────────────────────────── */}
        <div className="al-form-panel">

          {/* Mobile-only top logo */}
          <div className="al-mobile-logo" aria-hidden="true">
            <BrandMark />
            <span>PitchCraft</span>
          </div>

          {/* Mode headline */}
          <div className="al-form-header">
            <h2 className="al-form-title">
              {isLogin ? 'Welcome back' : 'Get started free'}
            </h2>
            <p className="al-form-subtitle">
              {isLogin
                ? 'Sign in to your workspace and continue building.'
                : 'Create your account and start winning proposals.'}
            </p>
          </div>

          {/* Clerk component injected here — appearance styled via CSS overrides */}
          <div className="al-clerk-shell">
            {children}
          </div>

          {/* Toggle link */}
          <p className="al-toggle">
            {isLogin ? "Don't have an account? " : 'Already have an account? '}
            <Link
              to={isLogin ? '/register' : '/login'}
              className="al-toggle-link"
            >
              {isLogin ? 'Sign up' : 'Sign in'}
            </Link>
          </p>

        </div>
      </div>

      {/* Footer */}
      <footer className="al-footer" aria-label="Footer">
        <span>© 2025 PitchCraft · </span>
        <a href="#" className="al-footer-link">Privacy</a>
        <span> · </span>
        <a href="#" className="al-footer-link">Terms</a>
      </footer>

    </div>
  )
}

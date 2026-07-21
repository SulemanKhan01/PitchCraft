/**
 * LoginPage.jsx
 * ─────────────────────────────────────────────────────────────────────────────
 * Auth Contract (PRESERVED — zero changes):
 *   • Clerk <SignIn /> — routing="hash", fallbackRedirectUrl="/chat"
 *   • All Clerk-internal handlers: OAuth, email/password, MFA, etc.
 *
 * Visual layer: wrapped in AuthLayout shell (new, non-breaking).
 * ─────────────────────────────────────────────────────────────────────────────
 */

import { SignIn } from '@clerk/clerk-react'
import AuthLayout from '../components/AuthLayout'

function LoginPage() {
  return (
    <AuthLayout mode="login">
      {/*
        Clerk <SignIn /> — ALL props preserved exactly.
        appearance prop styles it to match our design system
        via CSS overrides in AuthLayout.css (.al-clerk-shell .cl-*)
      */}
      <SignIn
        routing="hash"
        fallbackRedirectUrl="/chat"
        appearance={{
          variables: {
            /* Map Clerk's color system to our design tokens */
            colorPrimary:          '#7c3aed',
            colorBackground:       'transparent',
            colorText:             '#f4f2ff',
            colorTextSecondary:    '#b0adc0',
            colorInputBackground:  'rgba(32,28,48,0.9)',
            colorInputText:        '#f4f2ff',
            colorDanger:           '#f87171',
            borderRadius:          '12px',
            fontFamily:            'Inter, system-ui, sans-serif',
            fontSize:              '15px',
          },
        }}
      />
    </AuthLayout>
  )
}

export default LoginPage

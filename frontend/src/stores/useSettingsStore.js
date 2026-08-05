/**
 * useSettingsStore.js — Zustand store for PitchCraft Settings
 * Persisted to localStorage so settings survive page refreshes.
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const useSettingsStore = create(
  persist(
    (set) => ({
      // ── AI & RAG Engine ─────────────────────────────────────────────
      aiModel: 'gemini-3.1-flash-lite',
      scoreThreshold: 0.60,
      webSearchEnabled: true,
      maxChunks: 5,

      // ── Proposal & Cover Letter Defaults ────────────────────────────
      writingTone: 'enterprise',
      agencyName: '',
      portfolioUrl: '',
      signatureText: '',
      pdfTemplate: 'minimalist',

      // ── Appearance ──────────────────────────────────────────────────
      debugMode: false,
      autoScroll: true,

      // ── API Keys ────────────────────────────────────────────────────
      tavilyApiKey: '',

      // ── Actions ─────────────────────────────────────────────────────
      updateSettings: (patch) => set((state) => ({ ...state, ...patch })),
      resetSettings: () => set({
        aiModel: 'gemini-3.1-flash-lite',
        scoreThreshold: 0.60,
        webSearchEnabled: true,
        maxChunks: 5,
        writingTone: 'enterprise',
        agencyName: '',
        portfolioUrl: '',
        signatureText: '',
        pdfTemplate: 'minimalist',
        debugMode: false,
        autoScroll: true,
        tavilyApiKey: '',
      }),
    }),
    {
      name: 'pitchcraft-settings',
    }
  )
)

export default useSettingsStore

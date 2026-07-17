---
name: PitchCraft
description: Production-grade RAG system for proposal intelligence — fast, transparent, purposeful
colors:
  primary: "#7c3aed"
  primary-deep: "#6d28d9"
  primary-subtle: "rgba(124, 58, 237, 0.1)"
  bg: "#ffffff"
  bg-secondary: "#f9fafb"
  bg-sidebar: "#1e1b2e"
  text: "#374151"
  text-muted: "#9ca3af"
  text-heading: "#111827"
  text-sidebar: "#d1d5db"
  text-sidebar-active: "#ffffff"
  border: "#e5e7eb"
  border-focus: "#7c3aed"
  success: "#10b981"
  error: "#ef4444"
typography:
  display:
    fontFamily: "Inter, system-ui, -apple-system, sans-serif"
    fontSize: "clamp(1.5rem, 3vw, 1.75rem)"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Inter, system-ui, -apple-system, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Inter, system-ui, -apple-system, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 500
    lineHeight: 1.4
  mono:
    fontFamily: "Fira Code, ui-monospace, Consolas, monospace"
    fontSize: "0.875rem"
rounded:
  sm: "4px"
  md: "8px"
  lg: "12px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  2xl: "40px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "12px 20px"
  button-primary-hover:
    backgroundColor: "{colors.primary-deep}"
  button-secondary:
    backgroundColor: "{colors.bg-secondary}"
    textColor: "{colors.text-heading}"
    rounded: "{rounded.md}"
    padding: "12px 24px"
  input:
    backgroundColor: "{colors.bg}"
    textColor: "{colors.text-heading}"
    rounded: "{rounded.md}"
    padding: "12px 16px"
  sidebar-link:
    backgroundColor: "transparent"
    textColor: "{colors.text-sidebar}"
    rounded: "{rounded.md}"
    padding: "10px 12px"
  chat-bubble-user:
    backgroundColor: "{colors.primary}"
    textColor: "#ffffff"
    rounded: "{rounded.lg}"
    padding: "12px 16px"
  chat-bubble-assistant:
    backgroundColor: "{colors.bg-secondary}"
    textColor: "{colors.text}"
    rounded: "{rounded.lg}"
    padding: "12px 16px"
---

# Design System: PitchCraft

## 1. Overview

**Creative North Star: "The Speed Terminal"**

PitchCraft's design language is built for one thing: getting out of your way. Every interaction should feel instant, every surface purposeful. There is no decoration here — no gradients for beauty, no shadows for drama, no animation for delight. The interface is a conduit between the user and the pipeline's intelligence. When it works well, you forget it's there.

The palette is restrained: soft lavender as the sole accent, muted neutrals for everything else. Typography is functional — Inter does the work, no display fonts competing for attention. Elevation is flat by default, with shadows appearing only as responses to state. This is a tool that respects your time and attention.

**Key Characteristics:**
- Flat surfaces with functional shadows on interaction states only
- Single accent color (soft lavender) used sparingly — ≤10% of any screen
- Typography hierarchy through weight and size, not decoration
- Sidebar-first navigation with dark surface for visual separation
- Chat-first interaction model with clear user/AI distinction

## 2. Colors

The palette is intentionally minimal: one accent carries identity, neutrals do the heavy lifting.

### Primary
- **Soft Lavender** (#7c3aed): The brand accent. Used on primary buttons, active sidebar states, focus rings, and user chat bubbles. Its rarity is its power — it appears only where attention must land.
- **Deep Violet** (#6d28d9): Hover state for primary elements. Slightly darker, maintaining the same hue family.
- **Lavender Whisper** (rgba(124, 58, 237, 0.1)): Background tints for hover states, drag-over zones, and selected items. Low-opacity extension of the primary.

### Neutral
- **Ink** (#111827): Headings and primary text on light surfaces. High contrast, authoritative.
- **Slate** (#374151): Body text. Readable, comfortable, not harsh.
- **Mist** (#9ca3af): Secondary text, placeholders, timestamps. Low-emphasis information.
- **Cloud** (#f9fafb): Secondary backgrounds, card surfaces, code blocks. Subtle separation from the page.
- **Paper** (#ffffff): Primary background. Clean, spacious.
- **Obsidian** (#1e1b2e): Sidebar background. Dark surface for navigation, creates clear visual hierarchy.
- **Fog** (#e5e7eb): Borders, dividers, input strokes. Light structural lines.

### Status
- **Signal Green** (#10b981): Success states, upload confirmations. Used sparingly.
- **Alert Red** (#ef4444): Error states, destructive actions. High visibility when needed.

### Named Rules
**The 10% Rule.** The primary lavender occupies ≤10% of any given screen surface. Its rarity is the point — it signals importance through scarcity, not saturation.

**The Dark Sidebar Rule.** The sidebar is always Obsidian (#1e1b2e). It creates a permanent visual anchor and separates navigation from content. Never lighten the sidebar to match the content area.

## 3. Typography

**Display Font:** Inter (with system-ui fallback)
**Body Font:** Inter (with system-ui fallback)
**Label/Mono Font:** Fira Code (for code blocks and technical content)

**Character:** Inter is the workhorse — clean, legible, invisible. It does its job without calling attention to itself. The single-family approach means no visual friction between sections.

### Hierarchy
- **Display** (700, clamp(1.5rem, 3vw, 1.75rem), 1.2): Page titles. Appears once per page, at the top of the content area.
- **Title** (600, 1.125rem, 1.2): Section headings within pages. Used for card titles, group labels.
- **Body** (400, 1rem, 1.5): All readable content. Max line length: 65–75ch for comfortable reading.
- **Label** (500, 0.9375rem, 1.4): Interactive elements — buttons, links, input placeholders. Slightly smaller than body, weight carries the signal.
- **Caption** (400, 0.8125rem, 1.4): Metadata, timestamps, secondary information. Low-emphasis, high-density.

### Named Rules
**The Single Font Rule.** Inter is the only typeface in the UI. Fira Code appears only in code blocks. No display fonts, no decorative families. The typography system is about hierarchy through weight and size, not font variety.

## 4. Elevation

Flat by default. Shadows appear only as responses to state — hover, focus, active. Depth is conveyed through tonal layering (the sidebar's dark surface vs. the content's light surface) rather than lifted cards.

### Shadow Vocabulary
- **Focus Ring** (`0 0 0 2px rgba(124, 58, 237, 0.3)`): Applied to inputs and buttons on focus-visible. Indicates keyboard accessibility.
- **Subtle Lift** (`0 1px 3px rgba(0, 0, 0, 0.1)`): Used sparingly on dropdowns and popovers. Ambient, not structural.
- **Elevated Surface** (`0 10px 25px rgba(0, 0, 0, 0.1)`): Reserved for modals and overlays. Creates clear separation from the page.

### Named Rules
**The Flat-By-Default Rule.** Surfaces are flat at rest. Shadows appear only as a response to state (hover, elevation, focus). If a shadow exists without a state change, it's decorative — remove it.

**The No-Ghost-Card Rule.** Never combine `border: 1px solid` with `box-shadow` on the same element. Pick one: a solid border for structure, or a shadow for depth. Never both.

## 5. Components

### Buttons
- **Shape:** Gently curved edges (8px radius)
- **Primary:** Soft Lavender background (#7c3aed), white text, 12px 20px padding. Transitions background on hover to Deep Violet (#6d28d9).
- **Secondary:** Cloud background (#f9fafb), Slate text (#374151), 1px Fog border (#e5e7eb). Hover shifts to Fog background.
- **Disabled:** 50% opacity, cursor not-allowed. No shadow, no border change.

### Inputs
- **Style:** White background, 1px Fog border (#e5e7eb), 8px radius, 12px 16px padding. Clean, minimal, functional.
- **Focus:** Border shifts to Soft Lavender (#7c3aed) with a subtle focus ring (2px rgba of primary).
- **Placeholder:** Mist color (#9ca3af). Same contrast requirements as body text.
- **Error:** Border shifts to Alert Red (#ef4444). Error message appears below in the same color.
- **Disabled:** Cloud background (#f9fafb), Mist text, cursor not-allowed.

### Sidebar Navigation
- **Style:** Obsidian background (#1e1b2e), fixed 240px width, full viewport height.
- **Links:** Mist text (#d1d5db), 10px 12px padding, 8px radius. Hover shifts to white text with subtle background tint.
- **Active State:** Soft Lavender background (#7c3aed), white text. Clear, immediate indication of current page.
- **Logo:** White text, "Craft" in Soft Lavender. Simple, memorable.

### Chat Bubbles
- **User:** Soft Lavender background (#7c3aed), white text, 12px radius with bottom-right corner at 4px. Aligns right.
- **Assistant:** Cloud background (#f9fafb), Slate text (#374151), 1px Fog border, 12px radius with bottom-left corner at 4px. Aligns left.
- **Typing Indicator:** Three dots in Mist color, bouncing animation. Subtle, non-intrusive.

### Cards / Containers
- **Corner Style:** 12px radius (gentle curves, not pills)
- **Background:** Cloud (#f9fafb) for secondary surfaces, Paper (#ffffff) for primary.
- **Shadow Strategy:** Flat by default. Shadows only on hover/focus states.
- **Border:** 1px Fog (#e5e7eb) for structural separation. Never combined with shadows.
- **Internal Padding:** 24px standard, 16px compact.

## 6. Do's and Don'ts

### Do:
- **Do** use the 10% Rule: primary lavender on ≤10% of any screen surface. Its rarity signals importance.
- **Do** keep the sidebar Obsidian (#1e1b2e) at all times. It's the visual anchor.
- **Do** use weight and size for hierarchy, not font variety. Inter does everything.
- **Do** keep shadows flat-by-default. They appear only on hover, focus, or active states.
- **Do** use 8px radius for buttons/inputs, 12px for cards/bubbles. Consistent, not arbitrary.

### Don't:
- **Don't** combine border + box-shadow on the same element. Pick one, never both.
- **Don't** use gradient text (`background-clip: text`). Use a single solid color.
- **Don't** apply `border-radius: 24px+` on cards. Top out at 12px; full-pill is for tags/buttons only.
- **Don't** add decorative shadows on elements at rest. Shadows are responses to state, not decoration.
- **Don't** use emoji as icons in the UI. Use text labels or SVG icons instead.
- **Don't** create "ghost cards" with 1px borders + wide drop shadows. It's the most common AI tell.
- **Don't** use side-stripe borders (`border-left: 3px solid`) as accents. Use full borders, background tints, or nothing.
- **Don't** build generic AI chat apps — minimal interfaces with no structure, no personality, no pipeline transparency.
- **Don't** add bouncing, elastic, or spring animations. Ease-out-quart or quint only. Reduced motion is not optional.
- **Don't** use repeating-linear-gradient stripe backgrounds. Pure decoration, no function.

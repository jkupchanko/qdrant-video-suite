# Qdrant Spacing & Layout Specifications

This reference contains the spacing and layout specs for Qdrant website and landing pages, sourced from the Qdrant Brand Design System and verified against production Figma files.

---

## The 8-Point Grid System

The 8-point grid system defines spacing and sizing using multiples of 8 to create consistent, structured interfaces. By standardizing margins, paddings, gaps, and component dimensions, it removes arbitrary decisions and establishes a clear visual rhythm.

Using 8 as a base unit allows flexibility through smaller divisions like 4 or 2 while remaining aligned with digital screen scaling. In practice, the system functions as a spacing scale rather than a layout grid, with common values such as 8, 16, 24, 32, and 64. Typography aligns to the grid through line heights and vertical spacing to maintain consistent vertical rhythm.

The scale is continuous and extensible — spacing values grow indefinitely while remaining aligned to the same system.

### Spacing Scale

| Step | Value |
|---|---|
| 1 | 8px |
| 2 | 16px |
| 3 | 24px |
| 4 | 32px |
| 5 | 40px |
| 6 | 48px |
| ... | continues in 8px increments |

**4px half-steps** are allowed for micro-spacing (e.g., fine internal adjustments within small components), but 8px increments are the default.

### Off-Grid Exceptions (Website & Landing Pages Only)

Two values intentionally break the 8px grid on website and landing pages:

- **30px** — the column gap between layout columns / card grid items. This is optimized for the 1110px content width and should not be "corrected" to 32px.
- **165px** — the fixed side padding on every page. This is derived from centering 1110px of content within a 1440px viewport: (1440 − 1110) / 2 = 165.

---

## Page-Level Layout

All Qdrant website and landing pages are designed at a **1440px viewport width** with content centered inside a fixed container.

```
┌─────────────────── 1440px ───────────────────┐
│ 165px │◄──── 1110px content ────►│ 165px │
└──────────────────────────────────────────────┘
```

| Property | Value |
|---|---|
| Design viewport width | 1440px |
| Content area width | 1110px |
| Side padding (left + right) | 165px each |
| Column gap between grid items | 30px |
| Navigation bar height | 110px |
| Top announcement banner (when present) | 40px |

The **165px side padding** and **1110px content width** are constants — they do not change across pages. Content always starts at x=165 from the left edge of the viewport.

The **30px column gap** applies whenever items sit side by side in a grid (e.g., two cards, three cards, a split layout). This is consistent across all pages.

---

## Section Spacing

Sections are the top-level vertical blocks of a page. Each section manages its own vertical padding internally — there is no gap between sections at the page level.

### Hero Sections

Hero sections use the most generous padding to establish visual presence at the top of the page.

| Property | Value |
|---|---|
| Vertical padding | 80px – 120px (varies by page type) |
| Horizontal padding | 165px (standard) |

Shorter heroes (e.g., Pricing) tend toward 80px. Landing page heroes with more content use 120px top and bottom.

### General Sections

All other content sections (feature blocks, testimonial areas, architecture deep-dives, FAQ, customer logos, etc.) use vertical padding that varies based on content density and visual weight.

| Property | Value |
|---|---|
| Vertical padding | 80px – 120px |
| Horizontal padding | 165px (standard) |

Choose the value that lets the section breathe. Sections with dense content (FAQ, feature grids) may use 80px. Sections with a heading block followed by a large content area typically use 104px–120px.

### CTA Sections

Full-width CTA sections at the bottom of a page use consistent padding.

| Property | Value |
|---|---|
| Vertical padding | 120px |
| Horizontal padding | 165px (standard) |

### Heading-to-Content Gap

Within any section, the gap between the heading block (label + title + subtitle) and the content below it (cards, grids, code blocks) needs generous space. From the Figma data, this is typically **40px – 64px** depending on whether it's a primary section heading or a subsection heading. This is one of the most commonly under-spaced areas — err on the generous side.

---

## Narrower Content Contexts

Not all content uses the full 1110px width. Some patterns use narrower containers centered within the viewport for improved readability or visual focus.

| Context | Container width | How it's centered |
|---|---|---|
| Standard page content | 1110px | 165px side padding |
| Section heading text (constrained) | 730px – 980px | Centered within the 1110px container |
| FAQ section | 800px | Centered within the 1440px viewport |

The **730px heading constraint** is common for centered section titles where shorter line lengths improve readability. The **800px FAQ container** keeps question text scannable without stretching across the full content width.

---

## Border Radius Rules

Border radius values follow the 8px grid with one smaller step for compact elements.

| Value | When to use |
|---|---|
| 4px | Small elements: badges, pills, tags, copy buttons |
| 8px | Standard: cards, buttons, inputs, code blocks |
| 16px | Large: hero containers, CTA containers, prominent cards |

---

## CSS Custom Properties

Copy this block into any HTML/CSS project for Qdrant spacing and layout:

```css
:root {
  /* Spacing scale (8px grid) */
  --qdrant-space-1: 8px;
  --qdrant-space-2: 16px;
  --qdrant-space-3: 24px;
  --qdrant-space-4: 32px;
  --qdrant-space-5: 40px;
  --qdrant-space-6: 48px;
  --qdrant-space-7: 56px;
  --qdrant-space-8: 64px;

  /* Half-step (micro-spacing only) */
  --qdrant-space-05: 4px;

  /* Layout constants (website & landing pages) */
  --qdrant-viewport: 1440px;
  --qdrant-content-width: 1110px;
  --qdrant-side-padding: 165px;
  --qdrant-column-gap: 30px;

  /* Narrower content containers */
  --qdrant-narrow-content: 800px;

  /* Border radius */
  --qdrant-radius-sm: 4px;
  --qdrant-radius-md: 8px;
  --qdrant-radius-lg: 16px;

  /* Navigation */
  --qdrant-nav-height: 110px;
}
```

---

## Common Mistakes

**Using spacing values outside the 8px scale.** Values like 10px, 36px, or 50px don't exist in the system. Every spacing value should be a multiple of 8 (or 4 for micro-spacing). If a value feels "close enough" to an 8px multiple, use the actual multiple instead.

**Making section padding too small.** The minimum vertical padding on any section in a website or landing page is 80px. Nothing below that. If a section feels cramped, the padding is too low — not the content's fault.

**Not enough space between the heading block and the content below it.** This is the single most under-spaced area. The gap between a section's heading (label + title + subtitle) and the first piece of content (cards, grids, images) should be 40px–64px. If you're using 16px or 24px here, it's too tight for a marketing page.

**Confusing product UI spacing with marketing page spacing.** A 16px gap between elements works in a dashboard or app interface. On a landing page, that same gap looks cramped. Marketing pages need significantly more vertical breathing room than product UI — that's why section padding starts at 80px, not 32px.

**"Correcting" the 30px column gap to 32px.** The 30px gap between grid items is intentional. It's optimized for the 1110px content width — for example, three 350px cards + two 30px gaps = 1110px exactly. Changing it to 32px breaks the math and misaligns the layout.

---
name: qdrant-brand
description: "Qdrant visual brand guidelines and design system for creating on-brand presentations, documents, spreadsheets, landing pages, HTML artifacts, and any visual output. Use this skill whenever creating or styling any visual deliverable for Qdrant: slide decks, pitch decks, one-pagers, PDFs, Word docs, Excel reports, HTML pages, React components, email templates, social graphics, event banners, or any content that needs Qdrant's visual identity (colors, fonts, spacing, dark/light themes, component patterns). Also use when someone asks 'make it look like Qdrant', 'use our brand colors', 'style this with our design system', 'apply Qdrant branding', or needs to create any branded visual asset. Trigger this skill even when the user doesn't explicitly mention 'brand' if the task involves producing visual output that represents Qdrant. This skill handles the VISUAL side (colors, typography, layout, components). For MESSAGING (voice, tone, positioning, copy), also use the qdrant-messaging skill."
---

# Qdrant Brand Guidelines Skill

This skill ensures every visual deliverable produced for Qdrant is on-brand: correct colors, correct fonts, correct spacing, correct component patterns. It covers presentations, documents, spreadsheets, landing pages, HTML/React artifacts, and any other visual output.

Read this file fully before creating or styling any Qdrant-branded asset.

## How to Use This Skill

This file contains the core brand specifications: color palette, typography, spacing, themes, and layout principles. For deeper implementation details, read the relevant reference file:

| If the task involves... | Also read... |
|---|---|
| Exact hex values, RGB/HSL conversions, color tokens, CSS color variables, Python color constants | `references/color-specs.md` |
| Font metrics, type scale details, spacing tokens, slide/document font sizes, CSS typography variables | `references/typography-specs.md` |
| Page layout, spacing scale, section padding, grid columns, border radius, layout constants | `references/spacing-specs.md` |
| Logo placement, which lockup to use, embedding logos in HTML/React/PPTX/DOCX/XLSX | `references/logo-specs.md` + `assets/logos/` |
| Real-world examples of how to apply the brand to different deliverable types | `references/usage-examples.md` |
| Programmatic brand application (python-pptx, python-docx, openpyxl, HTML/CSS generation) | `scripts/brand_utils.py` (import and use directly) |

Multiple references may apply. For example, building a branded pitch deck would need `color-specs.md` (exact color values) + `typography-specs.md` (font sizes and spacing) + `usage-examples.md` (slide patterns) + `brand_utils.py` (to apply styles in code).

**Composability with qdrant-messaging:** This skill handles visuals. The `qdrant-messaging` skill handles words. When creating external-facing content, use both together: this skill for how it looks, qdrant-messaging for what it says.

---

## Brand Identity Overview

Qdrant's visual identity reflects its core product qualities: precision, performance, and engineering credibility. The design system is dark-first, developer-friendly, and built around a bold primary red against deep navy/charcoal backgrounds. It avoids generic SaaS aesthetics in favor of a look that signals technical depth.

**Design philosophy:** Infrastructure that lasts decades deserves a visual identity that's clean, precise, and functional. Every color choice, font weight, and spacing value is intentional.

---

## Color System

### Primary Palette

| Role | Name | Hex | When to use |
|---|---|---|---|
| **Primary (Qdrant Red)** | primary/500 | `#DC244C` | CTAs, buttons, key highlights, logo accent, interactive states. The signature Qdrant color. |
| **Primary Dark** | primary/800 | `#9E0D38` | Hover states, pressed buttons, dark-on-dark emphasis |
| **Primary Light** | primary/300 | `#FF8792` | Light theme accents, tags, subtle highlights |
| **Primary Lightest** | primary/50 | `#FDECEF` | Light theme background tints, alert backgrounds |

### Secondary Palette

| Role | Name | Hex | When to use |
|---|---|---|---|
| **Secondary (Violet)** | secondary/500 | `#6047FF` | Charts, data visualization accent, secondary CTAs, code highlights |
| **Secondary Dark** | secondary/800 | `#4325AE` | Dark theme secondary emphasis |
| **Secondary Light** | secondary/200 | `#C2C5FF` | Light theme secondary accents |
| **Teal** | teal/500 | `#009688` | Success states, positive metrics, tertiary accent |
| **Light Blue** | lightBlue/500 | `#03A9F4` | Informational elements, links in light theme |
| **Orange** | orange/500 | `#FF9800` | Warnings, attention-drawing elements |

### Neutral Palette (Dark Theme — Default)

| Role | Name | Hex | When to use |
|---|---|---|---|
| **Background** | neutral/950 | `#0B0F19` | Page background (dark theme default) |
| **Surface Level 1** | background/paper-elevation-1 | `#111824` | Cards, panels, elevated surfaces |
| **Surface Level 2** | background/paper-elevation-2 | `#141A2A` | Nested cards, dropdowns |
| **Surface Level 8** | background/paper-elevation-8 | `#212635` | Modals, popovers, highest elevation |
| **Text Primary** | text/primary | `#F0F3FA` | Headings, body text on dark backgrounds |
| **Text Secondary** | text/secondary | `#656B7F` | Captions, metadata, secondary info |
| **Text Disabled** | text/disabled | `#ABB1C7` | Placeholder text, disabled states |
| **Border** | neutral/700 | `#4E5366` | Subtle borders, dividers on dark backgrounds |

### Neutral Palette (Light Theme)

| Role | Name | Hex | When to use |
|---|---|---|---|
| **Background** | neutral/White | `#FFFFFF` | Page background (light theme) |
| **Surface** | background/paper-elevation-0 | `#F7F8FA` | Cards on light backgrounds |
| **Text Primary** | neutral/950 | `#0B0F19` | Headings, body text on light backgrounds |
| **Text Secondary** | neutral/600 | `#656B7F` | Secondary text on light backgrounds |
| **Border** | neutral/200 | `#D3D9EB` | Borders, dividers on light backgrounds |

### Data Visualization Colors

When creating charts, graphs, or data visualizations, use this ordered sequence:

1. `#DC244C` (Primary Red)
2. `#6047FF` (Secondary Violet)
3. `#009688` (Teal)
4. `#03A9F4` (Light Blue)
5. `#FF9800` (Orange)
6. `#9C27B0` (Purple)
7. `#4CAF50` (Green)
8. `#00BCD4` (Cyan)

### Gradient

Qdrant uses a signature gradient sparingly, for hero sections and premium visual moments:
- Primary gradient direction: from `#DC244C` to `#6047FF` (red to violet)
- This gradient maps to the brand's visual DNA and appears in the logo mark, hero backgrounds, and accent lines

### Color Rules

- **Dark theme is the default.** All web, presentation, and marketing materials default to dark backgrounds (`#0B0F19`) unless the context specifically calls for light (printed documents, light-mode UIs).
- **Never use Qdrant Red as a background fill for large areas.** It's an accent color for CTAs, highlights, and small elements.
- **Maintain contrast.** Text on dark backgrounds must use `#F0F3FA` (primary) or `#656B7F` (secondary). Never place light gray text on medium gray backgrounds.
- **Charts must be accessible.** Use the data visualization sequence above. Never rely on color alone to convey meaning.

---

## Typography

### Font Families

| Role | Family | Fallback Stack |
|---|---|---|
| **Primary (UI + Marketing)** | **Mona Sans** | `"Mona Sans", "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif` |
| **Monospace (Code)** | **Geist Mono** | `"Geist Mono", "JetBrains Mono", "Fira Code", "SF Mono", Consolas, monospace` |

**Mona Sans** is a variable font with weights from 200 to 900. Qdrant uses three primary weights: Regular (400), Medium (500), and SemiBold (600). Bold (700) is used sparingly for display type.

### Type Scale

| Token | Size | Weight | Line Height | Letter Spacing | Use |
|---|---|---|---|---|---|
| Display-2 | 104px | Bold (700) | 1.05 | -1.8px | Hero headlines (rare, impact) |
| Display-1 | 80px | SemiBold (600) | 1.05 | -1.8px | Major section heroes |
| H1 | 64px | SemiBold (600) | 1.1 | -1.5px | Page titles |
| H2 | 56px | SemiBold (600) | 1.1 | -0.5px | Section titles |
| H3 | 48px | SemiBold (600) | 1.1 | -0.5px | Subsection titles |
| H4 | 40px | SemiBold (600) | 1.2 | -0.5px | Card titles, feature headings |
| H5 | 32px | SemiBold (600) | 1.3 | -0.5px | Sub-headings |
| H6 | 24px | SemiBold (600) | 1.3 | -0.5px | Small headings, labels |
| Text-XL | 20px | Regular/SemiBold | 1.5 | -0.2px | Lead paragraphs, intro text |
| Text-LG | 18px | Regular/SemiBold | 1.5 | 0 | Body text (marketing) |
| Text-MD | 16px | Regular/SemiBold | 1.5 | 0 | Body text (default) |
| Text-SM | 14px | Regular/SemiBold | 1.5 | 0 | Captions, metadata |
| Text-XS | 12px | Regular | 1.5 | 0 | Fine print, badges |
| Mono-XL | 20px | Regular (400) | 1.5 | -0.2px | Code blocks, API examples |
| Mono-H6 | 24px | Regular (400) | 1.3 | -0.5px | Code headings, terminal titles |

### Typography Rules

- **Headings always use SemiBold (600)** unless Display-2 (Bold 700).
- **Body text uses Regular (400)** for readability, SemiBold for inline emphasis.
- **Negative letter-spacing** on headings H1 through H6 is intentional: it creates the dense, engineered feel.
- **Line height 1.5** for body text ensures readability. Headings use tighter line heights (1.05 to 1.3) for visual impact.
- **For presentations:** scale down proportionally. H1 becomes ~44pt, H2 ~36pt, body ~18pt. The ratios matter more than exact pixel values.
- **For documents (Word/PDF):** H1 = 28pt, H2 = 22pt, H3 = 18pt, Body = 11pt. Same weight rules apply.
- **Never apply gradient fills to typography.** Text must always be a single, solid color from the brand palette. Gradient text (e.g., CSS `background-clip: text`, PowerPoint gradient fills on text boxes, or any multi-color blended text effect) is not a Qdrant brand pattern and must never be used — on headings, body text, labels, or any other typographic element.

---

## Spacing System

Qdrant uses an 8px grid system. All spacing values are multiples of 8:

| Token | Value | Common use |
|---|---|---|
| 8 | 8px | Tight spacing (icon-to-text, chip padding) |
| 16 | 16px | Default element spacing |
| 24 | 24px | Card padding, section gap (small) |
| 32 | 32px | Section gap (medium) |
| 40 | 40px | Section padding |
| 48 | 48px | Large section gaps |
| 64 | 64px | Page section separation |
| 80 | 80px | Major section breaks |
| 88 | 88px | Hero section padding |

### Layout Grid

- **Max content width:** 1110px (centered within 1440px viewport)
- **Side margins:** 165px each on desktop (1440px)
- **Column gap:** 30px between cards in a grid
- **Card border-radius:** 8px (standard), 16px (large/hero cards)

---

## Component Patterns

### Buttons

| Type | Background | Text | Border | Border-Radius |
|---|---|---|---|---|
| **Primary CTA** | `#DC244C` | `#FFFFFF` | none | 8px |
| **Primary Hover** | `#CC1845` | `#FFFFFF` | none | 8px |
| **Secondary/Outline** | transparent | `#F0F3FA` | 1px `#4E5366` | 8px |
| **Ghost** | transparent | `#F0F3FA` | none | 8px |

### Cards (Dark Theme)

- Background: `#111824` (elevation-1)
- Border: 1px solid `#4E5366` or no border with subtle shadow
- Border-radius: 8px
- Padding: 24px
- Hover: subtle border color shift to `#656B7F`

### Pills / Tags

- Background: transparent or `#141A2A`
- Border: 1px solid `#4E5366`
- Text: `#F0F3FA` (Text-SM, 14px)
- Border-radius: full (pill shape)
- Padding: 4px 12px

### Code Snippets

- Background: `#111824`
- Header bar: `#141A2A` with tab for language name
- Font: Geist Mono, 14px
- Line numbers: `#656B7F`
- Code text: syntax-highlighted (standard dark theme)
- Border-radius: 8px
- Copy button in top-right corner

### Navigation

- Background: `#0B0F19` with slight blur/transparency
- Logo on left, menu items center, CTA button right
- Height: 110px (desktop), 64px (mobile)
- Menu text: Mona Sans, 14px, SemiBold, `#F0F3FA`

---

## Dark vs Light Theme

| Element | Dark (Default) | Light |
|---|---|---|
| Page background | `#0B0F19` | `#FFFFFF` |
| Card background | `#111824` | `#F7F8FA` |
| Primary text | `#F0F3FA` | `#0B0F19` |
| Secondary text | `#656B7F` | `#656B7F` |
| Borders | `#4E5366` | `#D3D9EB` |
| Primary CTA | `#DC244C` | `#DC244C` |
| CTA text | `#FFFFFF` | `#FFFFFF` |

The **Primary Red (#DC244C) stays the same in both themes.** It's always the accent.

---

## Logo Usage

All official logo files are bundled in `assets/logos/`. **Always use the supplied files — never recreate the logo in code.** For full details on which lockup to use, embedding instructions per deliverable type (HTML, PPTX, DOCX, XLSX), and do/don't rules, read `references/logo-specs.md`.

**Quick selection:**
- Dark background → `Qdrant-Logo-Red-White` (SVG or PNG)
- Light background → `Qdrant-Logo-Red-Black` (SVG or PNG)
- Icon only → `Qdrant-Brandmark-Red` (SVG or PNG)
- Social/avatar → `assets/logos/profiles/` (Circular or Square, Dark/Light/Transparent)
- Favicon → `assets/logos/favicon/Qdrant-Favicon.svg`

---

## Imagery & Illustration Style

- **3D renders:** Stylized 3D illustrations with glowing, translucent materials in red/violet/blue tones against dark backgrounds. Hero sections and feature highlights.
- **Photography:** Dark, moody treatment with color grading that matches the brand palette (cool blues, warm red accents).
- **Patterns:** Subtle dot grids, line patterns, and gradient meshes on dark backgrounds for texture.
- **Iconography:** Line-style icons, consistent stroke weight, using brand colors. Lucide icon set as the base.

---

## Deliverable-Specific Rules

### Presentations (pptx)

1. **Title slides:** Dark background (`#0B0F19`), large heading (H2/H3), Qdrant logo top-left, accent line or gradient element
2. **Content slides:** Dark background, heading in H5/H6, body in Text-LG, generous whitespace
3. **Data slides:** Use the data visualization color sequence, dark background, clean chart styling
4. **Section dividers:** Full-bleed dark or gradient background, large centered heading
5. **Final slide:** CTA with contact info, dark background, logo centered

### Documents (Word/PDF)

1. **Headers:** Mona Sans SemiBold, dark (`#0B0F19`) text on white
2. **Body text:** Mona Sans Regular, 11pt, `#303547` (neutral/800)
3. **Accent elements:** Use `#DC244C` for horizontal rules, bullet markers, callout borders
4. **Page margins:** 1 inch all sides
5. **Headers/footers:** Qdrant logo in header, page numbers in Text-SM

### Spreadsheets (xlsx)

1. **Header row:** Background `#0B0F19`, text `#F0F3FA`, SemiBold 11pt
2. **Alternating rows:** `#FFFFFF` and `#F7F8FA`
3. **Accent column headers:** `#DC244C` background for primary metric columns
4. **Data text:** Regular 10pt, `#303547`
5. **Chart styling:** Use data visualization color sequence

### HTML / React Artifacts

1. Use CSS custom properties (variables) mapping to the tokens above
2. Import Mona Sans from Google Fonts or CDN
3. Dark theme as default; support light theme via a class toggle
4. Follow the spacing grid (8px multiples)
5. Match component patterns (buttons, cards, pills) exactly

---

## Quick Reference

```
QDRANT BRAND QUICK REFERENCE
─────────────────────────────
Primary Red:     #DC244C
Secondary Violet: #6047FF
Background Dark:  #0B0F19
Surface Dark:     #111824
Text Light:       #F0F3FA
Text Secondary:   #656B7F

Font: Mona Sans (400, 500, 600, 700)
Mono: Geist Mono (400)
Grid: 8px base unit
Max Width: 1110px
Border Radius: 8px
```

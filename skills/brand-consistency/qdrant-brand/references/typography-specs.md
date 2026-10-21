# Qdrant Typography Technical Specifications

This reference contains the complete, machine-readable typography, spacing, and layout specifications extracted from the Qdrant Figma Design System. Use this when you need exact font metrics, spacing values, or layout dimensions for implementation.

## Table of Contents

1. [Required Stylistic Sets](#required-stylistic-sets)
2. [Typography Token Details](#typography-token-details)
3. [Spacing Tokens](#spacing-tokens)
4. [CSS Custom Properties (Typography & Layout)](#css-custom-properties-typography--layout)
5. [Presentation-Specific Values](#presentation-specific-values)
6. [Document-Specific Values](#document-specific-values)
7. [Python Implementation Examples (Typography)](#python-implementation-examples-typography)

---

## Required Stylistic Sets

Mona Sans is a variable font that supports multiple stylistic sets via OpenType features. **All Qdrant deliverables using Mona Sans MUST enable the following stylistic sets:**

| Set | Feature Code | Description | Effect |
|---|---|---|---|
| ss05 | `"ss05"` | Double-storey a | Replaces the single-storey "a" with a traditional double-storey form for improved readability and a more polished, professional appearance |
| ss06 | `"ss06"` | Double-storey g | Replaces the single-storey "g" with a traditional double-storey form, matching the double-storey "a" for visual consistency |

### How to Apply

**CSS (HTML/React artifacts, web pages):**

```css
html, body {
  font-family: "Mona Sans", "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-feature-settings: "ss05" on, "ss06" on;
}
```

**Python (python-pptx presentations):**

Note: python-pptx does not natively support OpenType feature settings. When generating PPTX files, this is a known limitation. If the presentation will be further edited in PowerPoint or Google Slides, the user can enable these features manually via the font dialog. For web-exported or HTML-based presentations, always use the CSS approach above.

**Python (python-docx documents):**

Note: python-docx does not natively support OpenType feature settings either. For Word documents, the stylistic sets can be enabled manually in the font advanced typography settings after generation. For any HTML or PDF export pipeline, always apply the CSS `font-feature-settings` rule.

**General rule:** Any context where Mona Sans is rendered via CSS **must** include `font-feature-settings: "ss05" on, "ss06" on;`. This applies to HTML artifacts, React components, landing pages, email templates, and any other web-based output.

---

## Typography Token Details

### Display Styles

```
Display-2/Bold
  family: "Mona Sans"
  weight: 700 (Bold)
  size: 104px
  lineHeight: 1.05 (109.2px)
  letterSpacing: -1.8px

Display-1/Semibold
  family: "Mona Sans"
  weight: 600 (SemiBold)
  size: 80px
  lineHeight: 1.05 (84px)
  letterSpacing: -1.8px
```

### Heading Styles

```
H1/Semibold
  family: "Mona Sans"
  weight: 600
  size: 64px
  lineHeight: 1.1 (70.4px)
  letterSpacing: -1.5px

H2/Semibold
  family: "Mona Sans"
  weight: 600
  size: 56px
  lineHeight: 1.1 (61.6px)
  letterSpacing: -0.5px

H3/Semibold
  family: "Mona Sans"
  weight: 600
  size: 48px
  lineHeight: 1.1 (52.8px)
  letterSpacing: -0.5px

H4/Semibold
  family: "Mona Sans"
  weight: 600
  size: 40px
  lineHeight: 1.2 (48px)
  letterSpacing: -0.5px

H5/Semibold
  family: "Mona Sans"
  weight: 600
  size: 32px
  lineHeight: 1.3 (41.6px)
  letterSpacing: -0.5px

H5/Bold
  family: "Mona Sans"
  weight: 700
  size: 32px
  lineHeight: 1.3 (41.6px)
  letterSpacing: -0.5px

H5/Regular
  family: "Mona Sans"
  weight: 400
  size: 32px
  lineHeight: 1.3 (41.6px)
  letterSpacing: -0.5px

H6/Semibold
  family: "Mona Sans"
  weight: 600
  size: 24px
  lineHeight: 1.3 (31.2px)
  letterSpacing: -0.5px

H6/Medium
  family: "Mona Sans"
  weight: 500
  size: 24px
  lineHeight: 1.3 (31.2px)
  letterSpacing: -0.5px

H6/Regular
  family: "Mona Sans"
  weight: 400
  size: 24px
  lineHeight: 1.3 (31.2px)
  letterSpacing: -0.5px
```

### Body Text Styles

```
Text-XL/Regular
  family: "Mona Sans", weight: 400, size: 20px
  lineHeight: 1.5 (30px), letterSpacing: -0.2px

Text-XL/Semibold
  family: "Mona Sans", weight: 600, size: 20px
  lineHeight: 1.5 (30px), letterSpacing: -0.2px

Text-LG/Regular
  family: "Mona Sans", weight: 400, size: 18px
  lineHeight: 1.5 (27px), letterSpacing: 0

Text-LG/Medium
  family: "Mona Sans", weight: 500, size: 18px
  lineHeight: 1.5 (27px), letterSpacing: 0

Text-LG/Semibold
  family: "Mona Sans", weight: 600, size: 18px
  lineHeight: 1.5 (27px), letterSpacing: 0

Text-MD/Regular
  family: "Mona Sans", weight: 400, size: 16px
  lineHeight: 1.5 (24px), letterSpacing: 0

Text-MD/Semibold
  family: "Mona Sans", weight: 600, size: 16px
  lineHeight: 1.5 (24px), letterSpacing: 0

Text-SM/Regular
  family: "Mona Sans", weight: 400, size: 14px
  lineHeight: 1.5 (21px), letterSpacing: 0

Text-SM/Medium
  family: "Mona Sans", weight: 500, size: 14px
  lineHeight: 1.5 (21px), letterSpacing: 0

Text-SM/Semibold
  family: "Mona Sans", weight: 600, size: 14px
  lineHeight: 1.5 (21px), letterSpacing: 0

Text-XS/Regular
  family: "Mona Sans", weight: 400, size: 12px
  lineHeight: 1.5 (18px), letterSpacing: 0
```

### Monospace Styles

```
Mono/XL/Regular
  family: "Geist Mono", weight: 400, size: 20px
  lineHeight: 1.5 (30px), letterSpacing: -0.2px

Mono/H6/Regular
  family: "Geist Mono", weight: 400, size: 24px
  lineHeight: 1.3 (31.2px), letterSpacing: -0.5px
```

---

## Spacing Tokens

| Token | px | rem (16px base) | Use |
|---|---|---|---|
| 8 | 8px | 0.5rem | Icon gap, chip padding |
| 16 | 16px | 1rem | Default element gap |
| 24 | 24px | 1.5rem | Card padding |
| 32 | 32px | 2rem | Section gap (small) |
| 40 | 40px | 2.5rem | Section padding |
| 48 | 48px | 3rem | Large section gap |
| 56 | 56px | 3.5rem | Feature section gap |
| 64 | 64px | 4rem | Page section break |
| 72 | 72px | 4.5rem | Large section break |
| 80 | 80px | 5rem | Major section break |
| 88 | 88px | 5.5rem | Hero padding |

---

## CSS Custom Properties (Typography & Layout)

Copy this block into any HTML/CSS project for Qdrant typography and layout theming:

```css
:root {
  /* Typography */
  --qdrant-font-family: "Mona Sans", "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --qdrant-font-mono: "Geist Mono", "JetBrains Mono", "Fira Code", "SF Mono", Consolas, monospace;
  --qdrant-font-weight-regular: 400;
  --qdrant-font-weight-medium: 500;
  --qdrant-font-weight-semibold: 600;
  --qdrant-font-weight-bold: 700;

  /* Stylistic Sets — REQUIRED for all Qdrant Mona Sans usage */
  --qdrant-font-features: "ss05" on, "ss06" on;

  /* Spacing */
  --qdrant-space-1: 8px;
  --qdrant-space-2: 16px;
  --qdrant-space-3: 24px;
  --qdrant-space-4: 32px;
  --qdrant-space-5: 40px;
  --qdrant-space-6: 48px;
  --qdrant-space-8: 64px;
  --qdrant-space-10: 80px;
  --qdrant-space-11: 88px;

  /* Layout */
  --qdrant-max-width: 1110px;
  --qdrant-side-margin: 165px;
  --qdrant-border-radius: 8px;
  --qdrant-border-radius-lg: 16px;
  --qdrant-column-gap: 30px;
}

/* Apply stylistic sets globally — double-storey a (ss05) and g (ss06) */
body {
  font-feature-settings: var(--qdrant-font-features);
}
```

---

## Presentation-Specific Values

### Slide Dimensions

- Standard: 13.333 x 7.5 inches (widescreen 16:9)
- In EMUs: width=12192000, height=6858000

### Font Sizes for Slides

| Role | Size (pt) | Weight | EMU equivalent |
|---|---|---|---|
| Title (hero) | 44 | SemiBold | Pt(44) |
| Section title | 36 | SemiBold | Pt(36) |
| Slide heading | 28 | SemiBold | Pt(28) |
| Subheading | 22 | SemiBold | Pt(22) |
| Body text | 18 | Regular | Pt(18) |
| Caption | 14 | Regular | Pt(14) |
| Footnote | 12 | Regular | Pt(12) |

### Slide Margins

- Left margin: 0.75 inches
- Top margin: 1.0 inches (below header)
- Right margin: 0.75 inches
- Bottom margin: 0.5 inches

---

## Document-Specific Values

### Page Setup

- Paper: Letter (8.5 x 11 inches)
- Margins: 1 inch all sides
- Header height: 0.5 inches
- Footer height: 0.5 inches

### Font Sizes for Documents

| Role | Size (pt) | Weight |
|---|---|---|
| Title | 28 | SemiBold |
| H1 | 22 | SemiBold |
| H2 | 18 | SemiBold |
| H3 | 14 | SemiBold |
| Body | 11 | Regular |
| Caption | 9 | Regular |
| Header/Footer | 9 | Regular |

### Paragraph Spacing for Documents

| Element | Space Before | Space After | Line Spacing |
|---|---|---|---|
| Title | 0pt | 12pt | 1.15 |
| H1 | 18pt | 6pt | 1.15 |
| H2 | 12pt | 4pt | 1.15 |
| H3 | 10pt | 3pt | 1.15 |
| Body | 0pt | 6pt | 1.5 |
| Caption | 0pt | 3pt | 1.3 |

---

## Python Implementation Examples (Typography)

### python-docx Font Size Constants

```python
from docx.shared import Pt, Inches, RGBColor, Cm

# Document-specific sizes:
DOC_H1_SIZE = Pt(28)
DOC_H2_SIZE = Pt(22)
DOC_H3_SIZE = Pt(18)
DOC_H4_SIZE = Pt(14)
DOC_BODY_SIZE = Pt(11)
DOC_CAPTION_SIZE = Pt(9)
```

# Qdrant Brand Usage Examples

Practical examples showing how to apply the Qdrant brand guidelines across different deliverable types. Each example demonstrates the correct application of colors, typography, spacing, and component patterns.

## Table of Contents

1. [HTML Landing Page Section](#html-landing-page-section)
2. [React Component (Feature Card)](#react-component-feature-card)
3. [Presentation Slide Patterns](#presentation-slide-patterns)
4. [Word Document Setup](#word-document-setup)
5. [Excel Report Styling](#excel-report-styling)
6. [Email Template](#email-template)
7. [Common Mistakes to Avoid](#common-mistakes-to-avoid)

---

## HTML Landing Page Section

This example recreates a landing page hero section matching the Qdrant Web Design system (see the Landing-Page-Template-Dark in Figma for reference). The template uses a 1440px viewport, 1110px content area with 165px side margins, and follows the dark-first approach.

```html
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-default: #0B0F19;
      --bg-elevation-1: #111824;
      --bg-elevation-2: #141A2A;
      --text-primary: #F0F3FA;
      --text-secondary: #656B7F;
      --primary-500: #DC244C;
      --primary-600: #CC1845;
      --secondary-500: #6047FF;
      --border-color: #4E5366;
      --font-family: "Mona Sans", "Inter", -apple-system, sans-serif;
      --font-mono: "Geist Mono", "JetBrains Mono", monospace;
      --max-width: 1110px;
      --border-radius: 8px;
    }

    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
      background: var(--bg-default);
      color: var(--text-primary);
      font-family: var(--font-family);
      font-size: 16px;
      line-height: 1.5;
    }

    .container {
      max-width: var(--max-width);
      margin: 0 auto;
      padding: 0 24px;
    }

    /* Hero Section */
    .hero {
      padding: 88px 0 80px;
      text-align: center;
    }

    .hero-pill {
      display: inline-block;
      font-size: 14px;
      color: var(--text-secondary);
      border: 1px solid var(--border-color);
      border-radius: 999px;
      padding: 4px 16px;
      margin-bottom: 24px;
    }

    .hero h1 {
      font-size: 56px;
      font-weight: 600;
      line-height: 1.1;
      letter-spacing: -0.5px;
      margin-bottom: 24px;
    }

    .hero p {
      font-size: 18px;
      color: var(--text-secondary);
      max-width: 730px;
      margin: 0 auto 40px;
      line-height: 1.5;
    }

    /* Buttons */
    .btn-primary {
      display: inline-block;
      background: var(--primary-500);
      color: #fff;
      font-family: var(--font-family);
      font-size: 16px;
      font-weight: 600;
      padding: 12px 24px;
      border-radius: var(--border-radius);
      border: none;
      cursor: pointer;
      text-decoration: none;
      transition: background 0.2s;
    }
    .btn-primary:hover { background: var(--primary-600); }

    .btn-outline {
      display: inline-block;
      background: transparent;
      color: var(--text-primary);
      font-family: var(--font-family);
      font-size: 16px;
      font-weight: 600;
      padding: 12px 24px;
      border-radius: var(--border-radius);
      border: 1px solid var(--border-color);
      cursor: pointer;
      text-decoration: none;
      margin-left: 16px;
    }

    /* Feature Cards */
    .features {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 30px;
      padding: 64px 0;
    }

    .card {
      background: var(--bg-elevation-1);
      border: 1px solid var(--border-color);
      border-radius: var(--border-radius);
      padding: 24px;
      transition: border-color 0.2s;
    }
    .card:hover { border-color: var(--text-secondary); }

    .card h3 {
      font-size: 24px;
      font-weight: 600;
      line-height: 1.3;
      letter-spacing: -0.5px;
      margin-bottom: 16px;
    }

    .card p {
      font-size: 16px;
      color: var(--text-secondary);
      line-height: 1.5;
    }

    .card .tag {
      display: inline-block;
      font-size: 14px;
      color: var(--text-primary);
      border: 1px solid var(--border-color);
      border-radius: 999px;
      padding: 4px 12px;
      margin-top: 16px;
      margin-right: 8px;
    }
  </style>
</head>
<body>
  <section class="hero">
    <div class="container">
      <span class="hero-pill">Why Teams Choose Qdrant</span>
      <h1>Recruitment Search is Broken at Scale</h1>
      <p>Many HR tech teams don't start with vector search. They start with
         Elasticsearch or PGVector, and hit a wall when the product needs
         compound filters at scale.</p>
      <a href="#" class="btn-primary">Get Started Free</a>
      <a href="#" class="btn-outline">Read the Docs</a>
    </div>
  </section>

  <section class="features">
    <div class="container" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 30px;">
      <div class="card">
        <h3>Semantic Job Matching</h3>
        <p>Match candidates to roles using meaning, not keywords. Dense vector
           search captures intent across languages and formats.</p>
        <span class="tag">Dense Vectors</span>
        <span class="tag">Payload Filters</span>
      </div>
      <div class="card">
        <h3>Real-time Candidate Search</h3>
        <p>Sub-second search across millions of profiles with compound filters
           for location, experience, skills, and availability.</p>
        <span class="tag">HNSW Index</span>
        <span class="tag">Quantization</span>
      </div>
      <div class="card">
        <h3>Multi-lingual Retrieval</h3>
        <p>Single query, multiple languages. Qdrant's multi-vector support lets
           you search across language boundaries natively.</p>
        <span class="tag">Multi-vector</span>
        <span class="tag">Named Vectors</span>
      </div>
    </div>
  </section>
</body>
</html>
```

### Key patterns in this example:
- Dark background (`#0B0F19`) as page base
- Cards on elevation-1 (`#111824`) with border (`#4E5366`)
- Hero uses H2 sizing (56px) with pill label above
- Two CTA buttons: primary (red) and outline (border)
- 3-column grid with 30px gap
- Tags/pills at bottom of cards with full border-radius
- Content centered within 1110px max-width

---

## React Component (Feature Card)

A reusable React component following Qdrant brand specs:

```jsx
import React from 'react';

const QdrantCard = ({
  icon,
  title,
  description,
  tags = [],
  onClick
}) => {
  return (
    <div
      onClick={onClick}
      style={{
        background: '#111824',
        border: '1px solid #4E5366',
        borderRadius: '8px',
        padding: '24px',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'border-color 0.2s',
        fontFamily: '"Mona Sans", "Inter", -apple-system, sans-serif',
      }}
      onMouseEnter={(e) => e.currentTarget.style.borderColor = '#656B7F'}
      onMouseLeave={(e) => e.currentTarget.style.borderColor = '#4E5366'}
    >
      {icon && <div style={{ marginBottom: '16px' }}>{icon}</div>}

      <h3 style={{
        fontSize: '24px',
        fontWeight: 600,
        lineHeight: 1.3,
        letterSpacing: '-0.5px',
        color: '#F0F3FA',
        margin: '0 0 16px 0',
      }}>
        {title}
      </h3>

      <p style={{
        fontSize: '16px',
        fontWeight: 400,
        lineHeight: 1.5,
        color: '#656B7F',
        margin: 0,
      }}>
        {description}
      </p>

      {tags.length > 0 && (
        <div style={{ marginTop: '16px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {tags.map((tag, i) => (
            <span
              key={i}
              style={{
                fontSize: '14px',
                color: '#F0F3FA',
                border: '1px solid #4E5366',
                borderRadius: '999px',
                padding: '4px 12px',
              }}
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

export default QdrantCard;
```

---

## Presentation Slide Patterns

### Title Slide (python-pptx)

```python
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank

# Dark background
bg = slide.background
fill = bg.fill
fill.solid()
fill.fore_color.rgb = RGBColor(0x0B, 0x0F, 0x19)

# Title text
txBox = slide.shapes.add_textbox(Inches(0.75), Inches(2.5), Inches(11.5), Inches(2))
tf = txBox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Qdrant: Vector Search
for Production AI"
p.font.size = Pt(44)
p.font.bold = False
p.font.color.rgb = RGBColor(0xF0, 0xF3, 0xFA)
p.font.name = "Mona Sans"
p.alignment = PP_ALIGN.LEFT

# Subtitle
p2 = tf.add_paragraph()
p2.text = "Series B Investor Update | Q1 2026"
p2.font.size = Pt(18)
p2.font.color.rgb = RGBColor(0x65, 0x6B, 0x7F)
p2.font.name = "Mona Sans"
p2.space_before = Pt(24)

# Accent line (Qdrant Red)
line = slide.shapes.add_shape(
    1,  # MSO_SHAPE.RECTANGLE
    Inches(0.75), Inches(2.2),
    Inches(2), Pt(4)
)
line.fill.solid()
line.fill.fore_color.rgb = RGBColor(0xDC, 0x24, 0x4C)
line.line.fill.background()
```

### Content Slide Pattern

```python
# Content slide with heading + body + card-like region
slide = prs.slides.add_slide(prs.slide_layouts[6])
bg = slide.background
fill = bg.fill
fill.solid()
fill.fore_color.rgb = RGBColor(0x0B, 0x0F, 0x19)

# Slide heading (H5 equivalent)
heading = slide.shapes.add_textbox(Inches(0.75), Inches(0.75), Inches(11.5), Inches(0.8))
tf = heading.text_frame
p = tf.paragraphs[0]
p.text = "Key Performance Metrics"
p.font.size = Pt(28)
p.font.color.rgb = RGBColor(0xF0, 0xF3, 0xFA)
p.font.name = "Mona Sans"

# Body text
body = slide.shapes.add_textbox(Inches(0.75), Inches(1.8), Inches(11.5), Inches(1.5))
tf = body.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Our infrastructure handles 2B+ daily queries across 500+ production deployments."
p.font.size = Pt(18)
p.font.color.rgb = RGBColor(0x65, 0x6B, 0x7F)
p.font.name = "Mona Sans"

# Metric card (simulated with a rounded rectangle)
card = slide.shapes.add_shape(
    5,  # MSO_SHAPE.ROUNDED_RECTANGLE
    Inches(0.75), Inches(3.5),
    Inches(3.5), Inches(2.5)
)
card.fill.solid()
card.fill.fore_color.rgb = RGBColor(0x11, 0x18, 0x24)
card.line.color.rgb = RGBColor(0x4E, 0x53, 0x66)
card.line.width = Pt(1)
```

---

## Word Document Setup

```python
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# Page margins
for section in doc.sections:
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

# Style configuration
style = doc.styles['Normal']
font = style.font
font.name = 'Calibri'  # Fallback; Mona Sans if installed
font.size = Pt(11)
font.color.rgb = RGBColor(0x30, 0x35, 0x47)

# Heading styles
for level, size in [(1, 28), (2, 22), (3, 18)]:
    heading_style = doc.styles[f'Heading {level}']
    heading_style.font.name = 'Calibri'
    heading_style.font.size = Pt(size)
    heading_style.font.bold = True
    heading_style.font.color.rgb = RGBColor(0x0B, 0x0F, 0x19)

# Add content
doc.add_heading('Qdrant Technical Overview', level=1)
doc.add_paragraph(
    'Qdrant is a high-performance, composable vector search engine '
    'built in Rust for production-grade AI workloads.'
)

# Accent horizontal rule (using paragraph border)
hr = doc.add_paragraph()
hr_fmt = hr.paragraph_format
# Set bottom border to Qdrant Red via XML manipulation
```

---

## Excel Report Styling

```python
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Performance Metrics"

# Column widths
ws.column_dimensions['A'].width = 30
ws.column_dimensions['B'].width = 18
ws.column_dimensions['C'].width = 18
ws.column_dimensions['D'].width = 18

# Header row styling
headers = ['Metric', 'Q1 2026', 'Q4 2025', 'Change']
header_fill = PatternFill(start_color="0B0F19", end_color="0B0F19", fill_type="solid")
header_font = Font(name="Calibri", size=11, bold=True, color="F0F3FA")

for col, header in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col, value=header)
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(horizontal='center', vertical='center')

# Accent header for key column
accent_fill = PatternFill(start_color="DC244C", end_color="DC244C", fill_type="solid")
accent_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
ws.cell(row=1, column=4).fill = accent_fill
ws.cell(row=1, column=4).font = accent_font

# Data rows with alternating fills
data_font = Font(name="Calibri", size=10, color="303547")
even_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
odd_fill = PatternFill(start_color="F7F8FA", end_color="F7F8FA", fill_type="solid")

data = [
    ['Daily Queries', '2.1B', '1.8B', '+16.7%'],
    ['P99 Latency', '12ms', '15ms', '-20.0%'],
    ['Active Clusters', '547', '489', '+11.9%'],
]

for row_idx, row_data in enumerate(data, 2):
    fill = even_fill if row_idx % 2 == 0 else odd_fill
    for col_idx, value in enumerate(row_data, 1):
        cell = ws.cell(row=row_idx, column=col_idx, value=value)
        cell.font = data_font
        cell.fill = fill
        cell.alignment = Alignment(horizontal='center' if col_idx > 1 else 'left')

wb.save('qdrant_metrics.xlsx')
```

---

## Email Template

```html
<div style="
  max-width: 600px;
  margin: 0 auto;
  font-family: 'Mona Sans', 'Inter', -apple-system, sans-serif;
  background: #0B0F19;
  color: #F0F3FA;
  padding: 40px 32px;
">
  <!-- Logo area -->
  <div style="margin-bottom: 32px;">
    <img src="qdrant-logo-white.svg" alt="Qdrant" height="32">
  </div>

  <!-- Heading -->
  <h1 style="
    font-size: 28px;
    font-weight: 600;
    line-height: 1.2;
    letter-spacing: -0.5px;
    margin: 0 0 16px 0;
  ">Your Weekly Vector Search Digest</h1>

  <!-- Body -->
  <p style="
    font-size: 16px;
    line-height: 1.5;
    color: #656B7F;
    margin: 0 0 24px 0;
  ">Here's what happened in the Qdrant ecosystem this week.</p>

  <!-- CTA Button -->
  <a href="#" style="
    display: inline-block;
    background: #DC244C;
    color: #FFFFFF;
    font-size: 16px;
    font-weight: 600;
    padding: 12px 24px;
    border-radius: 8px;
    text-decoration: none;
  ">Read the Full Update</a>

  <!-- Divider -->
  <hr style="
    border: none;
    border-top: 1px solid #4E5366;
    margin: 32px 0;
  ">

  <!-- Footer -->
  <p style="
    font-size: 12px;
    color: #656B7F;
    line-height: 1.5;
  ">Qdrant GmbH, Berlin, Germany</p>
</div>
```

---

## Common Mistakes to Avoid

### Color mistakes

| Mistake | Why it's wrong | Correct approach |
|---|---|---|
| Using `#DC244C` as a large background fill | Red is an accent, not a background. Large red areas overwhelm. | Use `#0B0F19` background, `#DC244C` for buttons and small highlights |
| Using `#000000` as background | True black is too harsh. Qdrant uses a deep navy. | Use `#0B0F19` (neutral/950) |
| Using gray text on gray cards | Insufficient contrast. | Use `#F0F3FA` on `#111824` cards; `#656B7F` only on `#0B0F19` backgrounds |
| Light theme with Qdrant dark colors for text | Mixing themes creates visual confusion. | Use the complete light theme palette (see SKILL.md) |

### Typography mistakes

| Mistake | Why it's wrong | Correct approach |
|---|---|---|
| Using Bold (700) for all headings | Qdrant headings are SemiBold (600). Bold is only for Display-2. | Use weight 600 for H1 through H6 |
| Positive letter-spacing on headings | Qdrant headings use negative letter-spacing for that tight, engineered feel. | Use -0.5px to -1.8px depending on heading level |
| Using sans-serif for code blocks | Code must be monospace for readability and brand consistency. | Use Geist Mono with the full fallback stack |
| Inconsistent font fallbacks | Missing fallbacks cause platform-specific rendering issues. | Always use the full fallback stack from the spec |

### Layout mistakes

| Mistake | Why it's wrong | Correct approach |
|---|---|---|
| Content wider than 1110px | Breaks the grid system, looks uncontrolled. | Max-width 1110px with auto centering |
| Spacing not on the 8px grid | Off-grid spacing looks subtly wrong. | All spacing values must be multiples of 8 |
| Cards without border-radius | Sharp corners don't match the brand. | 8px border-radius standard, 16px for hero cards |
| Missing hover states on interactive cards | Static cards feel dead. | Add border-color transition on hover |

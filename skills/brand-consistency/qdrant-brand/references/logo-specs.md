# Qdrant Logo Specifications

All official Qdrant logo files are bundled in `assets/logos/`. **Always use these files directly — never recreate, redraw, or approximate the logo.** Read this file before placing a logo in any deliverable.

---

## File Inventory

### SVG Logos (preferred for web, HTML, React, code-generated outputs)

| File | Brandmark | Wordmark | Background | Use when... |
|---|---|---|---|---|
| `svg/Qdrant-Logo-Red-White.svg` | Red (3-tone) | White | Dark | **Primary default.** Dark backgrounds, presentations, web dark theme |
| `svg/Qdrant-Logo-White.svg` | White (flat) | White | Dark | Monochrome on dark, embossed, single-color contexts |
| `svg/Qdrant-Logo-Black.svg` | Black (flat) | Black | Light | Monochrome on light, print single-color |
| `svg/Qdrant-Logo-Red-Black.svg` | Red (3-tone) | Black | Light | Light backgrounds, printed docs, light-theme web |
| `svg/Qdrant-Brandmark-Red.svg` | Red (3-tone) | — | Dark | Icon-only: favicon (SVG), app icons, tight spaces |
| `svg/Qdrant-Brandmark-White.svg` | White (flat) | — | Dark | Icon-only monochrome on dark |
| `svg/Qdrant-Brandmark-Black.svg` | Black (flat) | — | Light | Icon-only monochrome on light |

### PNG Logos (for documents, presentations, images, anywhere SVG isn't supported)

| File | Brandmark | Wordmark | Background |
|---|---|---|---|
| `png/Qdrant-Logo-Red-White.png` | Red (3-tone) | White | Dark |
| `png/Qdrant-Logo-White.png` | White (flat) | White | Dark |
| `png/Qdrant-Logo-Black.png` | Black (flat) | Black | Light |
| `png/Qdrant-Logo-Red-Black.png` | Red (3-tone) | Black | Light |
| `png/Qdrant-Brandmark-Red.png` | Red (3-tone) | — | Dark |
| `png/Qdrant-Brandmark-White.png` | White (flat) | — | Dark |
| `png/Qdrant-Brandmark-Black.png` | Black (flat) | — | Light |

### Favicon

| File | Use |
|---|---|
| `favicon/Qdrant-Favicon.svg` | Browser tab, PWA manifest |
| `favicon/Qdrant-Favicon.png` | Legacy favicon, 32×32 fallback |

### Social / Profile Lockups

These are pre-composed profile images with the brandmark centered on a background — ready to use as avatar/profile images on social platforms.

| File | Shape | Background | Use |
|---|---|---|---|
| `profiles/Circular/Qdrant-Profile-Circular-Dark.svg/.png` | Circle | Dark (`#0B0F19`) | Twitter/X, GitHub, LinkedIn avatar |
| `profiles/Circular/Qdrant-Profile-Circular-Light.svg/.png` | Circle | White | Light-background platforms |
| `profiles/Circular/Qdrant-Profile-Circular-Transparent.svg/.png` | Circle | Transparent | Overlay contexts |
| `profiles/Square/Qdrant-Profile-Squared-Dark.svg/.png` | Square | Dark (`#0B0F19`) | Discord, Slack workspace icon |
| `profiles/Square/Qdrant-Profile-Squared-Light.svg/.png` | Square | White | Light-background square avatars |
| `profiles/Square/Qdrant-Profile-Squared-Transparent.svg/.png` | Square | Transparent | Overlay on custom backgrounds |

---

## Which Logo to Use — Decision Tree

```
Is the background dark (≥50% dark, e.g. #0B0F19, #111824)?
├── YES → Use Red-White variant (Red brandmark + White wordmark)
│         SVG: Qdrant-Logo-Red-White.svg
│         PNG: Qdrant-Logo-Red-White.png
│
└── NO (light/white background)
    └── Use Red-Black variant (Red brandmark + Black wordmark)
          SVG: Qdrant-Logo-Red-Black.svg
          PNG: Qdrant-Logo-Red-Black.png

Need icon only (no wordmark)?
├── Dark bg → Qdrant-Brandmark-Red.svg (or White for monochrome)
└── Light bg → Qdrant-Brandmark-Red.svg (or Black for monochrome)

Single-color/monochrome context (1-color print, embossing, watermark)?
├── On dark → Qdrant-Logo-White.svg
└── On light → Qdrant-Logo-Black.svg

Social/profile image?
├── Platform uses circle crop → profiles/Circular/ variants
└── Platform uses square crop → profiles/Square/ variants
```

---

## Logo Dimensions & Clear Space

**Full logo (wordmark + brandmark) — viewBox 752×200**
- Aspect ratio: 3.76:1
- Recommended minimum width: 120px on screen, 40mm in print
- The brandmark occupies the leftmost ~173px of the 752px viewBox

**Brandmark only — viewBox 346.42×400**
- Aspect ratio: ~0.87:1 (nearly square, slightly portrait)
- Recommended minimum size: 24×28px on screen

**Clear space rule:** Maintain padding equal to the height of the "d" letter in "Qdrant" on all four sides. Never place other elements inside this zone.

---

## Embedding Logos by Deliverable Type

### HTML / React (inline SVG — best quality, fully scalable)

Read the SVG file from `assets/logos/svg/` and embed it inline. This allows CSS control over size and removes the HTTP request:

```html
<!-- Dark background page: inline the Red-White SVG -->
<header>
  <svg viewBox="0 0 752 200" width="180" height="48" xmlns="http://www.w3.org/2000/svg" aria-label="Qdrant">
    <!-- paste full SVG path content here -->
  </svg>
</header>
```

For React components, import as a component or use the raw SVG inline:

```jsx
// Option A: inline SVG (copy paths from Qdrant-Logo-Red-White.svg)
const QdrantLogo = ({ width = 180 }) => (
  <svg viewBox="0 0 752 200" width={width} height={width * (200/752)} aria-label="Qdrant" xmlns="http://www.w3.org/2000/svg">
    {/* paste SVG internals */}
  </svg>
);

// Option B: img tag with SVG src (works when file is served)
<img src="/assets/logos/svg/Qdrant-Logo-Red-White.svg" alt="Qdrant" width="180" />
```

### HTML via `<img>` tag

```html
<!-- Dark bg -->
<img src="assets/logos/svg/Qdrant-Logo-Red-White.svg" alt="Qdrant" width="160" height="43">

<!-- Light bg -->
<img src="assets/logos/svg/Qdrant-Logo-Red-Black.svg" alt="Qdrant" width="160" height="43">
```

### python-pptx (presentations)

Use the PNG variants. Pass the path to `add_picture()`:

```python
from pptx.util import Inches, Emu

# Dark slide: Red-White PNG
slide.shapes.add_picture(
    "assets/logos/png/Qdrant-Logo-Red-White.png",
    left=Inches(0.4),
    top=Inches(0.25),
    width=Inches(1.6)   # height auto-scales
)

# Light slide: Red-Black PNG
slide.shapes.add_picture(
    "assets/logos/png/Qdrant-Logo-Red-Black.png",
    left=Inches(0.4),
    top=Inches(0.25),
    width=Inches(1.6)
)

# Brandmark only (icon):
slide.shapes.add_picture(
    "assets/logos/png/Qdrant-Brandmark-Red.png",
    left=Inches(0.4),
    top=Inches(0.3),
    width=Inches(0.4)
)
```

### python-docx (Word documents)

Documents use a light (white) background, so use the Red-Black PNG:

```python
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# Add to header
section = doc.sections[0]
header = section.header
header_para = header.paragraphs[0]
header_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
run = header_para.add_run()
run.add_picture("assets/logos/png/Qdrant-Logo-Red-Black.png", width=Inches(1.4))
```

### openpyxl (spreadsheets)

```python
from openpyxl.drawing.image import Image as XLImage

img = XLImage("assets/logos/png/Qdrant-Logo-Red-Black.png")
img.width = 140   # pixels
img.height = 37   # maintain aspect ratio (752:200 ≈ 3.76:1)
ws.add_image(img, "A1")
```

---

## Logo Rules (Do / Don't)

**DO:**
- Always use the supplied files — SVG for web/code, PNG for office tools
- Match the logo variant to the background: Red-White on dark, Red-Black on light
- Maintain clear space on all sides
- Scale proportionally (never stretch or squish)
- Use the Brandmark-only files when the full wordmark doesn't fit

**DON'T:**
- Never recreate, trace, or approximate the logo in code (e.g. drawing polygons manually)
- Never recolor the logo — use only the supplied color variants
- Never add drop shadows, outlines, or effects to the logo
- Never place the logo on a busy, low-contrast, or red/violet background
- Never rotate or skew the logo
- Never use the Red brandmark on a red or pink background
- Never crop into the logo or use a partial lockup

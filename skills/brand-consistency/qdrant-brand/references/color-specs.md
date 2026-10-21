# Qdrant Color Technical Specifications

This reference contains the complete, machine-readable color specifications extracted from the Qdrant Figma Design System. Use this when you need exact color values for implementation.

## Table of Contents

1. [Complete Color Tokens](#complete-color-tokens)
2. [Color Conversion Tables](#color-conversion-tables)
3. [CSS Custom Properties (Color)](#css-custom-properties-color)
4. [Python Implementation Examples (Color)](#python-implementation-examples-color)

---

## Complete Color Tokens

### Primary Scale (Qdrant Red)

| Token | Hex | RGB | Use Case |
|---|---|---|---|
| primary/50 | `#FDECEF` | rgb(253, 236, 239) | Light theme tints, alert backgrounds |
| primary/100 | `#FCD7DD` | rgb(252, 215, 221) | Light badges, subtle accents |
| primary/200 | `#FAAEB3` | rgb(250, 174, 179) | Light interactive hover |
| primary/300 | `#FF8792` | rgb(255, 135, 146) | Light theme accents |
| primary/400 | `#FF516B` | rgb(255, 81, 107) | Bright accents, notifications |
| primary/500 | `#DC244C` | rgb(220, 36, 76) | **PRIMARY: CTAs, buttons, highlights** |
| primary/600 | `#CC1845` | rgb(204, 24, 69) | Hover state for primary buttons |
| primary/700 | `#BD0C3E` | rgb(189, 12, 62) | Active/pressed state |
| primary/800 | `#9E0D38` | rgb(158, 13, 56) | Dark emphasis, dark theme hover |
| primary/900 | `#850D35` | rgb(133, 13, 53) | Deepest red, used sparingly |

### Secondary Scale (Violet)

| Token | Hex | RGB | Use Case |
|---|---|---|---|
| secondary/50 | `#E5E8FF` | rgb(229, 232, 255) | Light tints |
| secondary/100 | `#DDE0FF` | rgb(221, 224, 255) | Light backgrounds |
| secondary/200 | `#C2C5FF` | rgb(194, 197, 255) | Light accents |
| secondary/300 | `#9494FF` | rgb(148, 148, 255) | Medium accents |
| secondary/400 | `#7E75FF` | rgb(126, 117, 255) | Interactive highlights |
| secondary/500 | `#6047FF` | rgb(96, 71, 255) | **SECONDARY: Charts, secondary CTAs** |
| secondary/600 | `#5F36F5` | rgb(95, 54, 245) | Hover state |
| secondary/700 | `#522AD8` | rgb(82, 42, 216) | Active state |
| secondary/800 | `#4325AE` | rgb(67, 37, 174) | Dark emphasis |
| secondary/900 | `#392689` | rgb(57, 38, 137) | Deepest violet |

### Neutral Scale

| Token | Hex | RGB | Use Case |
|---|---|---|---|
| neutral/White | `#FFFFFF` | rgb(255, 255, 255) | Light theme background, CTA text |
| neutral/50 | `#F0F3FA` | rgb(240, 243, 250) | Primary text on dark, light surfaces |
| neutral/100 | `#E2E7F5` | rgb(226, 231, 245) | Light borders |
| neutral/200 | `#D3D9EB` | rgb(211, 217, 235) | Light theme borders, dividers |
| neutral/300 | `#CAD0E5` | rgb(202, 208, 229) | Disabled borders |
| neutral/400 | `#ABB1C7` | rgb(171, 177, 199) | Disabled text |
| neutral/500 | `#898EA3` | rgb(137, 142, 163) | Placeholder text |
| neutral/600 | `#656B7F` | rgb(101, 107, 127) | Secondary text (both themes) |
| neutral/700 | `#4E5366` | rgb(78, 83, 102) | Dark theme borders |
| neutral/800 | `#303547` | rgb(48, 53, 71) | Document body text |
| neutral/900 | `#111824` | rgb(17, 24, 36) | Paper elevation 1, surface |
| neutral/950 | `#0B0F19` | rgb(11, 15, 25) | **Dark theme background** |
| neutral/Black | `#000000` | rgb(0, 0, 0) | True black (use sparingly) |

### Semantic / State Colors

| Token | Hex | RGB | Use Case |
|---|---|---|---|
| success/main | `#00897B` | rgb(0, 137, 123) | Success states, positive indicators |
| error/main | `#D32F2F` | rgb(211, 47, 47) | Error states, destructive actions |
| warning/main | `#EF6C00` | rgb(239, 108, 0) | Warning states |
| info/main | `#29B6F6` | rgb(41, 182, 246) | Informational states |

### Extended Palette (for charts and data visualization)

| Name | Hex | RGB |
|---|---|---|
| Teal 500 | `#009688` | rgb(0, 150, 136) |
| Light Blue 500 | `#03A9F4` | rgb(3, 169, 244) |
| Orange 500 | `#FF9800` | rgb(255, 152, 0) |
| Purple 500 | `#9C27B0` | rgb(156, 39, 176) |
| Green 500 | `#4CAF50` | rgb(76, 175, 80) |
| Cyan 500 | `#00BCD4` | rgb(0, 188, 212) |
| Indigo 500 | `#3F51B5` | rgb(63, 81, 181) |
| Yellow 500 | `#FFEB3B` | rgb(255, 235, 59) |
| Red 500 | `#F44336` | rgb(244, 67, 54) |

### Background Elevation System (Dark Theme)

| Level | Token | Hex | Use |
|---|---|---|---|
| 0 (page) | background/default | `#0B0F19` | Page background |
| 1 | background/paper-elevation-1 | `#111824` | Cards, panels |
| 2 | background/paper-elevation-2 | `#141A2A` | Nested surfaces, dropdowns |
| 8 | background/paper-elevation-8 | `#212635` | Modals, dialogs |
| 24 | background/paper-elevation-24 | `#2B303E` | Popovers, tooltips |

### Background Elevation System (Light Theme)

| Level | Token | Hex | Use |
|---|---|---|---|
| 0 (page) | background/paper-elevation-0 | `#F7F8FA` | Surface on white |
| Page | neutral/White | `#FFFFFF` | Page background |

---

## CSS Custom Properties (Color)

Copy this block into any HTML/CSS project for Qdrant color theming:

```css
:root {
  /* Primary */
  --qdrant-primary-50: #FDECEF;
  --qdrant-primary-100: #FCD7DD;
  --qdrant-primary-200: #FAAEB3;
  --qdrant-primary-300: #FF8792;
  --qdrant-primary-400: #FF516B;
  --qdrant-primary-500: #DC244C;
  --qdrant-primary-600: #CC1845;
  --qdrant-primary-700: #BD0C3E;
  --qdrant-primary-800: #9E0D38;
  --qdrant-primary-900: #850D35;

  /* Secondary (Violet) */
  --qdrant-secondary-50: #E5E8FF;
  --qdrant-secondary-100: #DDE0FF;
  --qdrant-secondary-200: #C2C5FF;
  --qdrant-secondary-300: #9494FF;
  --qdrant-secondary-400: #7E75FF;
  --qdrant-secondary-500: #6047FF;
  --qdrant-secondary-600: #5F36F5;
  --qdrant-secondary-700: #522AD8;
  --qdrant-secondary-800: #4325AE;
  --qdrant-secondary-900: #392689;

  /* Neutrals */
  --qdrant-neutral-white: #FFFFFF;
  --qdrant-neutral-50: #F0F3FA;
  --qdrant-neutral-100: #E2E7F5;
  --qdrant-neutral-200: #D3D9EB;
  --qdrant-neutral-300: #CAD0E5;
  --qdrant-neutral-400: #ABB1C7;
  --qdrant-neutral-500: #898EA3;
  --qdrant-neutral-600: #656B7F;
  --qdrant-neutral-700: #4E5366;
  --qdrant-neutral-800: #303547;
  --qdrant-neutral-900: #111824;
  --qdrant-neutral-950: #0B0F19;
  --qdrant-neutral-black: #000000;

  /* Semantic */
  --qdrant-success: #00897B;
  --qdrant-error: #D32F2F;
  --qdrant-warning: #EF6C00;
  --qdrant-info: #29B6F6;

  /* Backgrounds (Dark Theme) */
  --qdrant-bg-default: #0B0F19;
  --qdrant-bg-elevation-1: #111824;
  --qdrant-bg-elevation-2: #141A2A;
  --qdrant-bg-elevation-8: #212635;
  --qdrant-bg-elevation-24: #2B303E;

  /* Text (Dark Theme) */
  --qdrant-text-primary: #F0F3FA;
  --qdrant-text-secondary: #656B7F;
  --qdrant-text-disabled: #ABB1C7;

  /* Chart Colors */
  --qdrant-chart-1: #DC244C;
  --qdrant-chart-2: #6047FF;
  --qdrant-chart-3: #009688;
  --qdrant-chart-4: #03A9F4;
  --qdrant-chart-5: #FF9800;
  --qdrant-chart-6: #9C27B0;
  --qdrant-chart-7: #4CAF50;
  --qdrant-chart-8: #00BCD4;

  /* Borders */
  --qdrant-border-dark: 1px solid #4E5366;
  --qdrant-border-light: 1px solid #D3D9EB;

  /* Gradient */
  --qdrant-gradient-primary: linear-gradient(135deg, #DC244C, #6047FF);
}

/* Light theme override */
[data-theme="light"] {
  --qdrant-bg-default: #FFFFFF;
  --qdrant-bg-elevation-1: #F7F8FA;
  --qdrant-bg-elevation-2: #F0F3FA;
  --qdrant-text-primary: #0B0F19;
  --qdrant-text-secondary: #656B7F;
  --qdrant-text-disabled: #898EA3;
}
```

---

## Python Implementation Examples (Color)

### python-pptx Color Constants

```python
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor

# Primary palette
QDRANT_RED = RGBColor(0xDC, 0x24, 0x4C)
QDRANT_RED_DARK = RGBColor(0x9E, 0x0D, 0x38)
QDRANT_RED_LIGHT = RGBColor(0xFF, 0x87, 0x92)

# Secondary palette
QDRANT_VIOLET = RGBColor(0x60, 0x47, 0xFF)
QDRANT_VIOLET_DARK = RGBColor(0x43, 0x25, 0xAE)

# Neutrals
QDRANT_BG_DARK = RGBColor(0x0B, 0x0F, 0x19)
QDRANT_SURFACE_1 = RGBColor(0x11, 0x18, 0x24)
QDRANT_SURFACE_2 = RGBColor(0x14, 0x1A, 0x2A)
QDRANT_TEXT_PRIMARY = RGBColor(0xF0, 0xF3, 0xFA)
QDRANT_TEXT_SECONDARY = RGBColor(0x65, 0x6B, 0x7F)
QDRANT_BORDER = RGBColor(0x4E, 0x53, 0x66)

# Chart colors
CHART_COLORS = [
    RGBColor(0xDC, 0x24, 0x4C),  # Red
    RGBColor(0x60, 0x47, 0xFF),  # Violet
    RGBColor(0x00, 0x96, 0x88),  # Teal
    RGBColor(0x03, 0xA9, 0xF4),  # Light Blue
    RGBColor(0xFF, 0x98, 0x00),  # Orange
    RGBColor(0x9C, 0x27, 0xB0),  # Purple
    RGBColor(0x4C, 0xAF, 0x50),  # Green
    RGBColor(0x00, 0xBC, 0xD4),  # Cyan
]
```

### python-docx Color Constants

```python
from docx.shared import Pt, Inches, RGBColor, Cm

# Same RGBColor constants as above apply.
# Document-specific colors:
DOC_BODY_COLOR = RGBColor(0x30, 0x35, 0x47)  # neutral/800
DOC_HEADING_COLOR = RGBColor(0x0B, 0x0F, 0x19)  # neutral/950
DOC_ACCENT_COLOR = RGBColor(0xDC, 0x24, 0x4C)  # primary/500
```

### openpyxl Color Constants

```python
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# Header styles
HEADER_FILL = PatternFill(start_color="0B0F19", end_color="0B0F19", fill_type="solid")
HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="F0F3FA")

# Alternating row fills
ROW_FILL_EVEN = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
ROW_FILL_ODD = PatternFill(start_color="F7F8FA", end_color="F7F8FA", fill_type="solid")

# Accent header for key columns
ACCENT_FILL = PatternFill(start_color="DC244C", end_color="DC244C", fill_type="solid")
ACCENT_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")

# Data font
DATA_FONT = Font(name="Calibri", size=10, color="303547")

# Border
THIN_BORDER = Border(
    left=Side(style="thin", color="D3D9EB"),
    right=Side(style="thin", color="D3D9EB"),
    top=Side(style="thin", color="D3D9EB"),
    bottom=Side(style="thin", color="D3D9EB"),
)
```

---
name: face-framing-annotations-feedback
description: 2026-10-19 John on the NetworkChuck-style sample: his face looked stretched, the face cam was too small and too tight, and loops missed their words; use squares
metadata:
  type: feedback
---

On 2026-10-19 John reviewed the NetworkChuck-style sample: "Why does my face look like that?", the cam is "not really getting my face, might need to increase the size", and the annotations were "not circling stuff correctly. Maybe put squares".

The causes:
- The talk shot cropped a 2.05:1 strip and scaled it to 16:9, so his face was stretched vertically.
- The cam was 330x420 at a 1.35x zoom, which cut off his forehead and chin.
- The hand-drawn loops were placed by guessing, off the words they marked.
- A 1.46x docs zoom ran text under the cam.

**Why:** his own face is the first thing he checks, and a distorted or cropped face makes the whole edit look broken. Annotations that miss their target look careless.

**How to apply:**
- Always crop the face at the output's aspect ratio (`face_crop`, or a crop with height = width x 9/16 inside the bars). Never resize a crop of a different shape.
- Keep a face cam big enough to show the whole head: about 460x520 at a zoom near 1.0.
- Mark words with clean hand-drawn squares tight to the exact phrase rectangle. Capture word positions in the browser, including a word inside a sentence (`phrase>>word`). SVG diagram boxes need offsets from their labels.
- Fit zoomed docs so no text runs under the cam.
- Check annotations in full-size crops at their computed screen position, not only in thumbnail sheets.

Related: [[coding-channel-styles]], [[camera-code-small-window]], [[motion-design-feedback]].

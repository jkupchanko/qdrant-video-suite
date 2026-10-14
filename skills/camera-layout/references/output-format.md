# Camera Plan Output

## Human readable directions

Keep the spoken text in its original order, with one sentence per line.
Place directions beneath the passage they support.
Use the script’s existing Show and Transition labels rather than creating a competing layout.

[**Camera:** Small rectangular presenter window in the top right, 20% of frame width, with the established crop. **Show:** The simple concept diagram, with its labels outside the presenter region. **Transition:** Cut to the code view with the presenter hidden.]

Add no B roll block merely because the camera layout changes.
Preserve useful capture blocks already selected in the script.
Keep asset locations and recording instructions outside spoken narration.

## Machine handoff when needed

Use a frame size and an ordered scene list.
Each scene identifies the script section, a spoken cue, start and end targets, layout, presenter box, protected regions and transition intent.
Keep content coordinates relative to the video frame, excluding browser chrome around the recording.

Use normalized x, y, width and height values between 0 and 1.
The presenter field is null when it is hidden.
For a rectangle, record the crop aspect ratio separately from width and height fractions.
Mark examples as placeholders and timing as targets unless a real recording was measured.

```json
{
  "frame": {"width": 1920, "height": 1080},
  "timing_basis": "script targets",
  "presenter_source": "rectangular placeholder",
  "scenes": [
    {
      "id": "concept",
      "section": "Explain the connection",
      "spoken_cue": "Why would perro match dog?",
      "start_seconds": 50,
      "end_seconds": 62,
      "layout": "content_with_inset",
      "presenter": {
        "x": 0.77, "y": 0.05,
        "width": 0.20, "height": 0.266667,
        "shape": "rectangle", "crop_aspect_ratio": "4:3",
        "shot": "head and shoulders", "angle": "straight on"
      },
      "protected_regions": [
        {"role": "concept labels", "x": 0.06, "y": 0.20, "width": 0.65, "height": 0.50}
      ],
      "transition_intent": "Hide the presenter for the existing article insert."
    }
  ]
}
```

This is one scene example, not a complete video timeline.
A full sequence should preserve the supplied section boundaries and cover the intended recording without unintended gaps or overlaps.

## Final check

Confirm that each box fits inside the frame and preserves the requested crop.
Confirm that overlays do not cover protected regions.
Check the supplied words and section timings against the source script.
Separate existing footage, placeholders, illustrations and unrecorded results.

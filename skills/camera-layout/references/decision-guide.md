# Choosing Camera Space

## Begin with the viewer’s immediate task

Read the spoken passage and identify its main visual target.
An opening question can be delivered by the presenter, over the relevant object or through narration alone.
Code inspection, a returned result and a diagram explanation usually need room for the material being inspected.
Choose presenter presence when it adds useful guidance, personal explanation or connection.

A phrase is a cue, not an automatic layout command.
“Here is the code” can lead to content only when the code needs space.
“Let’s follow this” can support an inset when the view stays readable and the presenter window has a clear place.
“Compare these” asks for aligned alternatives; it does not automatically ask for half the frame to show a face.

## Six useful layouts

**Presenter full screen:** The person is the main visual object.
Use a supplied camera angle and an appropriate shot crop.
A centered medium shot is a useful starting choice for a calm explanation.
A voiceover video can omit this layout entirely.

**Content full screen:** Give the material the frame while the narration continues.
Use this for dense code, readable passages, tables, diagrams or detailed results.
Presenter visibility should not make the evidence harder to inspect.

**Small inset:** Place a rectangular presenter window over a reserved, quiet part of the content view.
In a horizontal video, 18% to 24% of frame width is a reasonable range to try during preparation, not an observed optimum.
Choose its size from the actual crop and the room available.
The suite example starts at 20% width, in the top right, with a 4:3 crop.

**Content dominant side panel:** Put content and presenter in separate regions.
The gallery gives the content about 70% of the width.
This can fit a simple walkthrough without making the presenter an overlay.
It is different from an inset and from equal halves.

**Equal presenter and content split:** Reserve half the width for each.
Use it only when both need comparable visual importance and the content stays readable at that size.
A short concept diagram can fit; an entire editor or dense result table may not.
An explanation can use this layout without implying that it is common in the reviewed sample.

**Two content views:** Use aligned halves for alternatives, before and after views or a comparison.
Keep the same input and scale where the comparison requires it.
The presenter can stay hidden.

## Size and protected content

Width percentage is not area percentage.
On a 1920 by 1080 frame, a 20% width inset is 384 pixels wide.
A 4:3 crop is 288 pixels high, or about 26.7% of frame height.
It occupies about 5.3% of the frame area.

For normalized coordinates, the frame’s top left is 0,0 and bottom right is 1,1.
Calculate normalized height as width fraction times frame aspect ratio divided by presenter aspect ratio.
The example box is x 0.77, y 0.05, width 0.20, height 0.266667.
It is a proposed layout, not a measurement from the source videos.

Identify text, diagram labels, controls, captions and results that must remain visible.
Keep the presenter outside those regions and inspect the layout at the intended viewing size.
If no suitable region remains, hide the presenter or create a justified separate panel.
For vertical video, recalculate geometry and test readability; do not reuse horizontal coordinates blindly.

## Continuity and transition intent

Keep the same inset corner, size, crop and shape within a continuous demonstration.
Removing and restoring it does not require moving it.
An intentional chapter change may choose a different arrangement, with a stated reason.

Attach a transition intent such as “cut from the presenter to the query” or “return to the same inset after the article.”
Keep effects, motion styling and timing refinements for the editing and transitions work.
Three sampled stills cannot establish how the source video transitioned between them.

## Counts and timing

Derive the number of presenter appearances from the planned sequence.
Adjacent passages using the same full screen shot form one appearance.
Do not apply a fixed face count to every video of the same length.
State whether times are supplied script targets or measured recording times.

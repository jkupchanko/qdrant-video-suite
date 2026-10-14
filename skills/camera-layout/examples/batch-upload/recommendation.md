# Recommendation: a three minute upload tip

Made with the script library's process (extract the material, identify the viewer, establish what can be
shown, choose the story, match the duration), then handed to the camera skill.

**Audience:** A developer who has a Qdrant collection and is loading their first real dataset into it with
the Python client. Comfortable with Python; new to how the client sends points.

**Funnel stage:** Action. They are about to run the upload.

**Purpose:** Replace a loop of single upserts with one batched upload call, and know how to check that it
worked.

**Length:** Three minutes, regular horizontal video.

**Available material:** The Python client code for both versions (a loop of `upsert` calls and one
`upload_points` call with a batch size), the terminal output of each run with its elapsed time, the
collection's point count from the dashboard, and the docs page for `upload_points`. No invented benchmark:
the script asks the viewer to read the elapsed time they measure.

**Recommended structure:** [The Practical Tip](../../../technical-video-script-library/Styles/06%20The%20Practical%20Tip.md).

**Reason:** One small action (send points in batches instead of one at a time) that can be demonstrated in
order and checked with an observable result (the elapsed time and the point count). No background lesson is
needed.

**Alternative, if useful:** The Guided Process, if the video also covered embedding the data and creating
the collection; that would be a longer, multi-step video.

**Output:** The finished script, `script.md`, written with one spoken sentence per line, section timings,
and bracketed Show and Transition cues. Camera lines were then added by the camera skill: `script-with-camera.md`.

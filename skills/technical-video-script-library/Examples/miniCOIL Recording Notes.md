# Recording Notes

[Read the recommendation](miniCOIL%20Recommendation.md)

[Read the script](miniCOIL%20Five%20Minute%20Script.md)

## Status and scope

This is a recording plan with code views checked against the published implementation.
The model and live retrieval have not been executed for this example.
Run the prepared demonstration before filming and use the outputs it actually produces.

The recording starts with the encoder loaded and the collection populated.
Put installation, model download and indexing instructions in the accompanying resources.
Explain that prepared starting state in the video.

## The demonstration

Use one English only collection named `video_demo` with three short passages.
Store each passage’s full text in its payload so the results can be read on screen.

**Passage 1:** A dog ran through the park after a red ball.

**Passage 2:** This soup uses onion, garlic and fresh tomato.

**Passage 3:** Astronomers found a new star in a distant galaxy.

**First query:** `perro corriendo en el parque`

**Intended answer:** Passage 1.

**Second query:** `sopa con cebolla y ajo`

**Intended answer:** Passage 2.

The intended answers are human judgments, not assertions about the model’s output.
Use the same three passages for both searches.
Record the actual returned text and the rank of the intended answer, or record that it is missing.
Do not put translated copies of the passages in the collection for this demonstration.

## Prepare the published encoder

Use the published `Jocana/minicoil-en-es` checkpoint and its `MiniCoilEncoder` implementation.
The published retrieval example loads the checkpoint and encoder code through `snapshot_download`.
Use its preparation flow, encode these English passages with `lang="en"`, and store them in the collection before recording.

The complete published example and technical checks are linked in the separate [technical notes](../Research/miniCOIL%20Technical%20Notes.md).

## Code view 1   Encode the passage and question

Show these calls after the prepared encoder has been loaded.

```python
passage = "A dog ran through the park after a red ball."
question = "perro corriendo en el parque"

document_values = encoder.encode_sparse(passage, lang="en")
query_values = encoder.encode_sparse(
    question, lang="es", is_query=True
)
```

Highlight the language first, then the query flag.
The document encoding also belongs to the preparation stage used to populate the collection.

## Code view 2   Configure the sparse vector

Show the relevant part of the collection configuration.
It is created once during preparation.

```python
sparse_vectors_config={
    "minicoil": models.SparseVectorParams(
        modifier=models.Modifier.IDF
    )
}
```

Keep the vector name consistent between stored passages and searches.
The surrounding creation call uses `vectors_config={}` for this sparse only collection.

## Code view 3   Search the prepared collection

The published encoder returns a dictionary of positions and values.
Define this small conversion helper during preparation, then show the search call.

```python
def to_sparse(values):
    entries = sorted(values.items())
    return models.SparseVector(
        indices=[position for position, value in entries],
        values=[value for position, value in entries],
    )

results = client.query_points(
    collection_name="video_demo",
    query=to_sparse(query_values),
    using="minicoil",
    limit=3,
).points
```

The helper depends on `models` from `qdrant_client`.
Store each prepared passage as a point with `vector={"minicoil": to_sparse(document_values)}` and its text in the payload.
Each passage needs its own document encoding and unique point identifier.
For the second search, encode the new question with `lang="es", is_query=True` before running the same call.

## Describe the actual result

Use the main script’s inspection questions regardless of the outcome.
Add a short observation that matches the recording.

**If the intended passage is first:** The passage we wanted is first in this result.

**If it appears farther down:** The passage is here, but it is below another result.

**If it is missing:** The passage we wanted did not appear in this result.

Follow an unexpected outcome with a useful check of the language settings, stored vectors and trained concept coverage.
State the observed outcome before explaining a possible cause.
Do not claim a cause until it has been inspected.

## Visual treatment

Keep the query, document language and returned passage readable.
Use a quiet background and one emphasis color for the words or line being discussed.
Use actual output for results and numerical vector values.
Label diagrams as illustrations.
The context illustration explains the mechanism; it is separate from the two live searches.

## Camera continuity

Plan four full screen presenter appearances: the hook, the transition into code, the opening of the limit section and the closing.
Use a centered medium shot for each full screen appearance.
Keep the smaller presenter window in the top right at roughly 20% of the screen width, with the same crop whenever it returns.
Hide the face while inspecting code and results and while showing either article insert.
The exact changes are attached to the relevant passages in the script.

## Two selective B roll inserts

The script contains two capture blocks.
The live search and code walkthrough are the main recording.

**Insert 1:** Open the article’s introduction and locate the home and casa illustration.
Capture a steady close view with the words and shared positions readable.
Use it during the sentence that introduces home and casa, then return to the demonstration.

**Insert 2:** Open From Words to Concepts and locate the illustration beneath One Slot per Concept.
Capture the parts contrasting the animal and baseball meanings of bat.
Use it during the sentence explaining how surrounding words help represent the intended meaning.

The article link and capture instructions appear only in the two selected B roll blocks in the script.
Those blocks can be passed to a separate recording workflow.
Keep later animation proposals outside these capture requests.
No supporting footage has been recorded for this example.

## Readable code and results

Show one code view at a time.
Crop to the relevant lines and pause while explaining them.
Keep the collection name and vector name consistent across views.
Move between views through the same query, passage or concept rather than unrelated decorative footage.

Natural typing and clicks can support the live actions.
If music is used, keep it quiet enough that every spoken word is clear.
Use a change of visual when it helps explain a new action or question.

## Timing and rehearsal

The section times in the script add up to five minutes.
They are editing targets, not a measured reading time.
Rehearse the narration with the two live searches and the time needed to inspect code and results.
Remove repeated explanation if the recording runs long.
Leave reading time for the actual output.

## The viewer’s practice task

Prepare a few short passages with answers the viewer can judge.
Try one familiar question, one context sensitive question and one subject specific term.
Record the intended answer and its observed rank for each query.

This is a small learning exercise.
Use the checkpoint only within its applicable license terms; the technical notes identify the current restriction.

# Technical Notes for the Search Example

Checked on October 13, 2026.
These notes support preparation and factual review.
The spoken script keeps source references out of its narration.

[Return to the recommendation](../Examples/miniCOIL%20Recommendation.md)

## Matching mechanism

The article describes shared English and Spanish concepts, eight values per concept block and values that depend on surrounding text.
The video uses one familiar word pair and a labeled context illustration to explain that mechanism.
It does not present the illustration as a measured retrieval result. [Article](https://qdrant.tech/articles/minicoil-en-es/)

## Encoder and search calls

The published retrieval example loads the checkpoint through `snapshot_download`, imports its encoder implementation and stores sparse vectors in Qdrant.
It demonstrates `lang`, `is_query=True`, conversion from a dictionary to `SparseVector`, and `query_points` with a named vector. [Published retrieval example](https://github.com/pentoai/minicoil-en-es/blob/main/scripts/eval/published_model_retrieval_check.py)

The encoding guide states that Qdrant must apply IDF at query time through `Modifier.IDF`.
It also documents the query flag and the encoder’s dictionary output. [Encoding and scoring guide](https://github.com/pentoai/minicoil-en-es/blob/main/docs/06-inference-and-scoring.md)

## Coverage and context

The released model has a limited trained vocabulary.
Words outside its concepts use ordinary word matching.
That preserves lexical signals, including some shared names and cognates, but does not supply an absent translation relationship.
This is why the recording plan asks viewers to test their own subject terms. [Encoding and scoring guide](https://github.com/pentoai/minicoil-en-es/blob/main/docs/06-inference-and-scoring.md)

## License and evaluation

The article states that the current checkpoint and training code are released under CC BY NC 4.0 and restricted to noncommercial use.
Check that the planned use fits those terms before using the checkpoint in a project or recording. [Article](https://qdrant.tech/articles/minicoil-en-es/)

The article’s reported evaluation uses a judged passage pool and a concept covered query slice.
The video therefore makes no universal ranking, speed or cost claim.
The article and repository also differ in one translated baseline figure; no benchmark number is used in this script. [Article](https://qdrant.tech/articles/minicoil-en-es/), [Implementation repository](https://github.com/pentoai/minicoil-en-es)

## Verification boundary

The script and code views were reviewed against the published sources.
The model was not downloaded or run, and no search result is supplied as verified output.
The prepared demo must be run before recording.
The script’s inspection wording and recording notes allow successful, lower ranked or missing results to be described accurately.

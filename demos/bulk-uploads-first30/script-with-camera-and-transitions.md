# Bulk Uploading Data to Qdrant: first 30 s, all layers

Edited from the Zoom take (cut list in `bulk_uploads_first30_cutlist.md`). Camera, B-roll and transitions
applied by the suite's rules; nothing added that the model videos do not do.

## Hook   0:00 to 0:15

When uploading large amounts of data, Qdrant isn't just storing vectors.
It's also handling payloads, indexes, and much more in the background.
There's no single configuration that works for all workloads.
So we will go over a few different options and best practices you can try.

[**Camera:** FULL, centred, mirrored take, bars top and bottom. Holds through the hook (the corpus holds the opening about 20 s). Jump cuts between takes carry the alternating 1.00 / 1.06 push. **Transition:** cut.]

## Dense vs. Sparse Vectors   0:15 to 0:30

Before we start, dense and sparse vectors.

[**Camera:** FULL, unchanged. The person's set-up line. **Transition:** cut.]

Dense vectors typically use HNSW,
while sparse vectors use a separate sparse index.

[**Camera:** NONE. The two index names are the one thing in these 30 s the viewer benefits from seeing; the Bulk Uploading docs page has a section on exactly that. Face off for 5 s, back on the next line. **Show:** The "Why Vector Type Matters" section of the bulk data import page, slow push into the heading. **Transition:** the docs card pushes in from the right, 0.3 s (the one push in the opening); cut back to the face.]

[**B-ROLL: https://qdrant.tech/documentation/production-operations/bulk-data-import/ | dense vectors use HNSW while sparse vectors use a separate sparse index | section: Why Vector Type Matters | 5s]

Because they're indexed differently, they can create different memory and performance considerations during bulk uploads.

[**Camera:** FULL. The reason is the person's line; the face has been off 5 s. **Transition:** cut.]

## Count

Layouts: FULL and NONE. Camera lines: 4. Transitions: cuts, one push at 0:19.6 where the docs card arrives.
B-roll: one docs section (Why Vector Type Matters, bulk data import page), recorded by the B-roll skill, finished in the house card.

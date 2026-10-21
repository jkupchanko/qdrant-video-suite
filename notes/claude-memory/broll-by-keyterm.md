---
name: broll-by-keyterm
description: "John's rule that B-roll is chosen by the script's key terms (named things get the matching page section; general lines get no B-roll)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 39bc7a71-3509-46be-83a4-5d1a21b62df7
  modified: 2026-10-15T04:47:30.583Z
---

John said (2026-10-14): when doing B-roll, read the script for key terms. If a line talks about something specific (HNSW, quantization, payload index, batch size, shards, on_disk, an identifier), look for that term on the article/docs page and show that section. If the line is general talk, no B-roll: stay on him. Generic words (memory, disk, vectors, uploads) do not count. One insert per section.

**Why:** B-roll should prove the thing being named, not decorate; random page scrolls under general lines read as filler.
**How to apply:** `broll-recorder/scripts/keyterms.py SCRIPT.md URL` makes the call per line and writes the markers; the rule is in the B-roll SKILL.md and camera-markers rule 2. For the Bulk Uploads video the page is https://qdrant.tech/documentation/production-operations/bulk-data-import/ and its sections map one to one onto the script's options and best practices. Related: [[broll-recorder-skill]], [[script-three-layers]].

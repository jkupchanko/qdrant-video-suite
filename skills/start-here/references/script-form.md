# The script's form

Every build reads the script, so it has to be in this form. The full syntax of each piece is in its own skill; this page
puts them together and lists the mistakes that have cost a build.

## An example

```markdown
<!-- Source page: https://qdrant.tech/documentation/production-operations/bulk-data-import/ -->

# Bulk Uploading Data to Qdrant

## Hook   0:00 to 0:15

When uploading large amounts of data, Qdrant isn't just storing vectors.

[**Lower third:** John Kupchanko | Developer Relations Engineer | 5 s]

It's also handling payloads, indexes, and much more in the background.

[**Camera:** FULL, centred. Holds through the hook. **Transition:** cut.]

## Dense vs. Sparse Vectors   0:15 to 0:30

Dense vectors typically use HNSW, while sparse vectors use a separate sparse index.

[**Camera:** NONE. The two index names must be read. **Show:** the "Why Vector Type Matters" section. **Transition:** soft 0.8 s into the card; soft back to the face.]

[B-ROLL: https://qdrant.tech/documentation/production-operations/bulk-data-import/ | dense vectors use HNSW while sparse vectors use a separate sparse index | section: Why Vector Type Matters | 3s | name: dense_vs_sparse]

Because they're indexed differently, they create different memory and performance considerations during bulk uploads.

[**Camera:** FULL. The reason is the presenter's line. **Transition:** soft 0.8 s back to the face.]
```

## The pieces

| piece | form | where | details |
|---|---|---|---|
| source page | `<!-- Source page: URL -->` | top of the file | the docs page the B-roll and figures come from |
| sections | `## Name   m:ss to m:ss` | each section | the times are planned, not measured; the cut sets the real ones |
| spoken lines | plain sentences | under each heading | everything not in brackets, a heading or a comment is said aloud and searched for in the take |
| name card | `[**Lower third:** NAME \| TITLE \| 5 s]` | after the line it comes in on, near the start | brand-consistency; the build refuses to start without one |
| camera call | `[**Camera:** FULL / SMALL / NONE ... **Transition:** ...]` | under a passage where the camera changes | camera-layout's `references/camera-markers.md`; between calls the camera holds |
| transition | `**Transition:** ...` inside every camera call | | transitions skill; Qdrant house rule: soft, about 0.8 s, into and out of cards; cuts between face takes. The style applies that rule by itself and reads only `white flash` (a chapter) from the field, so the rest is for the people reading the script |
| not looking | `[**Not looking:** 0:41 to 0:46. Face not shown here.]` | under the line, after the raw edit | where the eyes leave the lens in the approved cut; the face is hidden there and something else stays on screen |
| B-roll | `[B-ROLL: URL \| spoken line \| section: X \| 5s \| name: n]` | right after the line it illustrates | broll-recorder's `references/script-markers.md`; only on lines that name something specific |

## Mistakes that have cost a build

- **A B-roll marker without `name:`.** The recorder names the clip from the line, but the style looks for the name in the
  marker, finds none, and the clip never reaches the video (laptop test build, 2026-10-20). Always give `name:`.
- **A marker placed after a later line than the one it quotes.** The clip lands on the quoted line, the list card for the
  later line lands on top of it, and the B-roll shows for 0.05 s (Bulk Uploads preview, 2026-10-21). Put each marker
  directly under the line it quotes.
- **Bold around the label: `[**B-ROLL: ...]`.** The recorder does not see it as a marker. Write `[B-ROLL: ...]`.
- **Fewer than two fields after the URL.** The style and the review need at least `URL | spoken line | ...`.
- **Notes written as plain text.** An introduction or production note in plain sentences is read as a spoken line, and
  the review reports it as missing from the cut. Put notes in `<!-- ... -->` comments.
- **No name card.** The build stops and asks for one.

# The model videos: real joins to copy

Of the 50 audited, these are the most-watched that share the Qdrant format (a presenter who cuts to screens,
20%+ of the time on the face, 1.5+ shot changes a minute). Their joins between face and screen are what
`examples/reference-joins.mp4` shows, 1.5 s each side, with the measured kind in the label. Nothing in that
reel is re-created; every clip is the original video.

| video | views | face on screen | shot changes/min | how they join face and screen |
|---|---|---|---|---|
| Jeff Su, AI Agents Clearly Explained | 5.4M | 36% | 9.5 | 15 cuts, 5 animated card moves, 1 fade-white (soft 0.46 s) |
| Futurepedia, First AI Agent in 25 Minutes | 4.4M | 35% | 5.6 | 16 cuts, 3 slides, 4 animated, 2 fade-white (0.42 s) |
| Jeff Su, Basics of AI | 3.6M | 53% | 6.8 | 11 cuts, 3 fade-white, 1 slide, 2 animated (0.48 s) |
| NetworkChuck, host ALL your AI locally | 2.7M | 84% | 6.9 | 17 cuts, 4 animated (0.13 s) |
| Aaron Jack | 2.4M | 81% | 12.7 | 6 cuts, 6 animated (0.14 s) |
| NetworkChuck, You SUCK at Prompting | 0.9M | 74% | 8.2 | 24 cuts, 3 slides, 2 dissolves, 11 animated (0.23 s) |
| Dan Martell, Build Your First AI Agent | 0.8M | 74% | 17.8 | 53 cuts, 1 animated |
| Aishwarya Srinivasan, Vector Databases Explained | 0.3M | 76% | 7.8 | 16 cuts, 3 slides, 1 animated (0.17 s) |

What they have in common, and what the rules in SKILL.md are built from:

- The join between the face and a screen is a cut in every one of them. Soft moves are a minority used for
  one job each: Futurepedia and Aishwarya push a card in; Jeff Su flashes white at a chapter; NetworkChuck
  dissolves twice in 24 minutes.
- Where a soft move exists it is short: 0.13 to 0.48 s. Nobody holds a dissolve.
- The "animated" entries are cards and graphics flying in over a shot that stays, with motion blur. They
  are element work with one entrance style per video, not a shot-to-shot transition.
- The rest of the motion is labels and captions popping over a held shot: 60 to 90% of visible changes in
  these videos. That is where their energy comes from, not from transitions.

Caveats: 360p copies were audited, so very fast moves can blur into "animated"; the face share comes from the
camera audit, where tiny corner windows are undercounted.

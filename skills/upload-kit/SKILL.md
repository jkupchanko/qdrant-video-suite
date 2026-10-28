---
name: upload-kit
description: What YouTube asks for besides the video, for the video suite - a title, a description that leads with what the viewer gets and links the docs in its first lines, chapters made from the script's sections and timed by where the cut actually says them, and every page the video shows - all checked against YouTube's rules and against 49 popular technical videos. Use it whenever someone asks for a title, a description, chapters, timestamps, "what do I put on YouTube", "help me upload this", "write the description", "add chapters", or is about to publish a finished video, even if they do not name this skill. The video-builder's upload step runs it; start-here hands its files over at the end. It does not make thumbnails yet.
---

# Upload kit

A finished video still needs words around it before anyone can find it. This skill drafts them from the script, so
nothing is typed twice, and checks them before they go up.

## The rules (the numbers behind each: [references/research.md](references/research.md))

1. **Chapters are the script's sections**, each starting where the cut first says one of its lines. YouTube shows
   them only when the first is at 0:00, there are three or more, and each lasts 10 s: anything else is a fix. A
   section the cut leaves under 10 s joins the next, both titles kept.
2. **The description leads with the hook and what the viewer gets** (the intro's opening line, then its "by the end,
   you'll have..." or "you can..." line), then the docs page as a link in the first lines, the chapters, and every page the video shows. No
   placeholder address (`YOUR-CLUSTER...`) ever reaches it.
3. **Three titles to choose from**, by the 49 videos' numbers: 20 to 70 characters, the product named, what the
   viewer gets, no emoji, at most one word in capitals. The person picks; the script's title is only the draft.
4. **No thumbnail yet.** Made by hand until the suite can do it properly.

## Run it

The video-builder runs it after the review (`upload/` in the build). By hand:

```bash
S=~/.claude/skills/upload-kit/scripts
python $S/upload_kit.py SCRIPT.md CUT/cutlist.md --out UPLOAD      # title.txt, description.txt, chapters.txt, checked
python $S/upload_kit.py --check UPLOAD                             # again, after the person edits the files
python $S/chapters.py SCRIPT.md CUT/cutlist.md                     # the chapters alone
python $S/selftest.py                                              # the checks still catch what they should
```

Chapters are timed on the cut. If the finished video adds anything before the cut (an intro card), pass its length
as `chapters.py --offset SECONDS`.

## Handing it over

start-here's last step: propose three titles, show the description, write the chosen title into `title.txt`, run
`--check`, and hand over `title.txt` (YouTube: Title) and `description.txt` (YouTube: Description; its chapters become
the progress bar's).

## Files

- `scripts/upload_kit.py`: the draft and the checks. `scripts/chapters.py`: chapters from the script and the cut.
- `scripts/audit_upload.py`: the 49-video research. `scripts/selftest.py`: planted faults, caught.
- `references/research.md`.

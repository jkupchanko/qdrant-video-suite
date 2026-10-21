---
name: start-here
description: The front door of the video suite. Walks a person from "I want to make a video" to a finished, reviewed video in eight steps, in order - what they have, one of two ways in (an existing script or video, or starting from scratch), the script questions, approving the script, picking an editing style, recording, building, reading the review. Use it whenever someone wants to make, start, plan or get help with a technical or Qdrant video, says "where do I start", "help me get started", "I have a script", "I have a recording", "I have an idea for a video", "new video", or names a topic they want to teach on video, even if they do not mention the suite or any skill. When the person already has an approved script and a raw take and explicitly asks to build ("build it", "run the build"), go straight to step 7 (video-builder); "help me make the video" starts at step 1.
---

# Start here

The README's pathway, run by Claude. The script controls the whole video: who it is for, what it teaches, what is on
screen, the B-roll, the camera, the transitions and the name card. Every step below exists to get the script right; once
it is right, the other skills do their part from what they have already learned.

## How to run it

- **One step at a time, in order.** Each step ends with something from the person (an answer, an approval, a file).
  Do not run ahead: a build started on an unapproved script wastes an hour and a half.
- **Say where they are.** Open each step with its number and name ("Step 3 of 8: the script questions"), so the person
  always knows what has happened and what comes next.
- **Ask only what is missing.** If the conversation, the script, a file or memory already answers a question, say what
  you are using ("name card: John Kupchanko, Developer Relations Engineer, from the script") and move on.
- **Ask in one message, then wait.** Group a step's questions together; never drip them one per turn. The waits are:
  after step 1 (if they have not said what they have), after 2b (their explanation), after step 3 (the answers), after
  step 4 (approval), after step 5 (the style) and after step 6 (the take). The step 2a report has no wait of its own:
  send it together with the step 3 questions, and ask about its suggestions there.
- **Show, do not attach.** The script goes in the reply, inline, every time it changes. Save it to a file as well.
- **Skip what is done.** A step the person has already answered still gets its header and one line saying what they
  told you ("Step 1 of 8: you are starting from scratch, on hybrid search"). Someone with an approved script and a take
  starts at step 5 or 7; say which steps are skipped and why.

The other skills live beside this one in `~/.claude/skills/` (they are in the suite repo under `skills/`). The script
library is a guide, not a skill: read it from `~/.claude/skills/technical-video-script-library/`, or from the repo's
`skills/technical-video-script-library/` if it is not installed.

## Step 1 of 8: what do you have?

Ask what they are working with, unless they already said:

> What do you have so far? For example: a finished script, a rough draft, a recording, notes, a docs page, or just the
> topic.

Then pick the way in:

- **A script, a draft, or a recording** -> step 2a.
- **Nothing written yet** (a topic, an idea, notes, a docs link) -> step 2b.

Note any recording now (where it is, whether it was read from a script): it decides step 6. **Check that it is a raw
take, not an edit.** Signs of an edit: a cut list or README beside it that describes cuts, a length close to the
script's own (a raw take with retakes runs well over it), black bars, a mirrored picture (text in the room reads
backwards). The build cuts and mirrors the take itself, so an edited file comes out cut twice and mirrored back. If it
looks edited, say so and ask for the raw recording.

## Step 2a of 8: review what they have

Read every file they give you in full. Then check the script against the suite's form
([references/script-form.md](references/script-form.md)) and report, in one message:

1. **Who it is for and what it is for.** Say what the script implies (viewer, what they know, the goal). If it is unclear,
   that becomes a question in step 3.
2. **What is missing from the form.** Section headings with times, the source-page note, the name card, a camera call
   wherever the camera changes, a transition on every call, B-roll markers with all their fields. Missing pieces are filled
   in at step 4, not now.
3. **Where the B-roll should go.** Run the key-term pass, which decides line by line which lines name something the docs
   page shows:
   `python ~/.claude/skills/broll-recorder/scripts/keyterms.py SCRIPT.md DOCS_URL --out keyterms.md`
   DOCS_URL is the script's source-page note, else the URL in its B-roll markers, else ask for it in step 3.
   Compare the pass with the script's own markers: a marker on a general line, or a specific line with none. The pass
   proposes, the script's author decides: when a marker already sits on a specific line and its section matches what is
   said there, keep it even if the pass picks another section, and say why. One marker may cover two lines in a row.
   (Plain-text notes in the script show up in both tools as junk rows: ignore them, they get fixed in step 4.)
4. **Where the camera should be.** Run the planner as a check on the script's calls:
   `python ~/.claude/skills/camera-layout/scripts/camera_plan.py SCRIPT.md --out camera_plan.md`
5. **Suggested changes to the lines.** A line a viewer cannot follow, a section that runs long, a claim the docs do not
   support. Give the change and the reason; the person decides.

**A recording but no script:** transcribe it (faster-whisper, `small.en`, as the editing skill does) and write the
script from what was said, keeping their words. Show it, then continue as above.

## Step 2b of 8: explain what you want to teach

Ask them to explain the topic in their own words, in whatever form is easiest: a few sentences, a list of notes, a docs
link, a rough voice memo. Say that structure comes later; nothing needs to be organised yet. If they give a docs page,
read it.

When the topic is broad (hybrid search covers dense and sparse vectors, fusion, the Query API), invite them to name the
angle they care about, without choosing one for them. End with one line on what step 3 will ask, so they know what is
coming, but keep its questions for step 3: the answers often come out of their explanation.

## Step 3 of 8: the script questions

Both ways in meet here. Ask only the questions their material has not answered, in one message (the reasons are in the
script library's `Audience and Purpose.md` and `Recommendation Guide.md`, and the brand skill's
`references/intake.md`):

1. **Who is watching?** A developer, a customer, someone new to Qdrant?
2. **What do they already know** about this subject?
3. **What is the goal?** Understand something, choose between options, or be able to do a task?
4. **How long** should it be, and is it a regular video or a vertical short?
5. **Which docs page** is it about? (The B-roll and on-screen figures come from it.)
6. **Your name and title** for the name card.

A docs link they gave earlier answers question 5. A name and title from memory or an earlier script are used, but shown
for a yes in the same message ("Name card: John Kupchanko, Developer Relations Engineer. Right?"): a misspelled name is
the most visible mistake a video can have.

Then recommend **one** of the ten structures in the script library's `README.md` (the practical tip, the guided process,
the comparison and choice, and so on) with one concrete reason, and name an alternative only when the difference would
help them choose. Follow `Recommendation Guide.md`.

When a take already exists and will be used, the structure is mostly fixed by what was recorded: name the structure it
follows, and recommend a different one only if they are willing to re-record. Compare the take's words with the
script's (the editing skill transcribes it) and suggest changing the script to what was said, since the take cannot
change.

## Step 4 of 8: write the script and get it approved

Write (or complete) the script in the suite's form: [references/script-form.md](references/script-form.md). All three
layers, every time, without being asked:

1. **The lines**, in the chosen structure (the structure's page under `Styles/` says what each section does).
2. **The B-roll**: a marker only on lines that name something specific the docs page shows; the key-term pass proposes,
   and the markers agreed in step 3 stand (broll-recorder).
3. **The camera calls and transitions**: a call wherever the camera changes, required at the opening, wherever something
   must be read, at section boundaries and at the close (camera-layout); a transition value on every call, following the
   Qdrant house rule of soft 0.8 s changes into and out of cards (transitions).

Plus the name card after the first line, and the source-page note at the top.

Show the whole script inline, save it next to their files (e.g. `TOPIC_script.md`), and ask for approval. Make every
change they ask for in the script itself and show it again. Do not move on until they approve.

## Step 5 of 8: pick an editing style

Show the options and ask which one; default to Listed Sections if they have no preference:

| style | what it looks like | note |
|---|---|---|
| Listed Sections (`list`) | the video as a numbered list, current item lit, the docs page's own figures and code | builds itself from the script and the page; the list comes from docs sections with a "Best fit" line, so a script that never names such a section leaves the screen empty (say so) |
| Animated Board | one board per section that builds as they speak; five looks | planned by hand for each video |
| Code Report | fast and visual: real docs with highlights, captions, title cards | planned by hand for each video |

The style pages are in the suite repo under `styles/`. For Animated Board or Code Report, say that its plan is written
for this video before the build, and that this takes longer.

## Step 6 of 8: record, or hand over the take

If there is no recording yet, they record now. Tell them:

- Read the approved script. Retakes and stumbles are fine: the editing skill keeps the last complete take of every line.
- Look at the lens. When the eyes leave it, the face goes off screen in the edit, so glances at notes cost screen time.
- Any webcam or Zoom recording works; a tag in the corner is covered.

Then ask where the file is. If they already have a take that was recorded from a different version of the script, warn
that lines never said will be listed as NO TAKE FOUND.

## Step 7 of 8: build

Hand over to the **video-builder** skill: it runs every skill in order and ends with the review. Everything it asks in its
own "Ask first" section is answered by now; pass it on rather than asking again.

```bash
python ~/.claude/skills/video-builder/scripts/build.py --take RAW.mp4 --script SCRIPT.md --out BUILD_DIR --label "Topic, style" --style list
```

Run it in the background. It takes roughly an hour and a half for 3.5 minutes of video. Give a one-line update as each
stage finishes (from `BUILD_DIR/build.json`). A stage that fails stops the build even though the command exits 0: read
`BUILD.md` and the stage's log, not the exit code.

## Step 8 of 8: read the review

Follow video-builder's "After the build" section: read `review/report.md`, look at `review/sheet.jpg` and every fix
frame yourself, and separate real faults from false alarms before reporting.

Report to the person in plain words: where the video is, what the review found, what you are fixing and how. Most fixes
go back into the script (step 4), and the build re-runs from the stage they affect (`--from STAGE --redo STAGE`). When
the person spots a fault the review missed, find it, fix it at its skill, and add a review check and a self-test case for
it (video-review).

When the review is clean and the person has watched it, the video is done.

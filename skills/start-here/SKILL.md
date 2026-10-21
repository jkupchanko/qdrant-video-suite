---
name: start-here
description: The front door of the video suite. Walks a person from "I want to make a video" to a finished, reviewed video in eight steps, in order - what they have, who the video is for and what it should do (always asked), the script reviewed or written for that viewer, approving the script, picking an editing style, recording, building, checking. Use it whenever someone wants to make, start, plan or get help with a technical or Qdrant video, says "where do I start", "help me get started", "I have a script", "I have a recording", "I have an idea for a video", "new video", "start over", or names a topic they want to teach on video, even if they do not mention the suite or any skill. When the person already has an approved script and a raw take and explicitly asks to build ("build it", "run the build"), go straight to step 7 (video-builder); "help me make the video" starts at step 1.
---

# Start here

The README's pathway, run by Claude, as a conversation that narrates where the person is. The script controls the
whole video. The person decides who the video is for, what it should do, how long it is and how it looks; the skills
decide the camera, the B-roll and the transitions from what they have learned, and show their choices in the script.

## How to run it

- **One step at a time, in order.** Each step ends with something from the person. Do not run ahead: a build started on
  an unapproved script wastes an hour and a half.
- **Narrate.** Open every step with a small map of the eight steps (done, here, coming up): an inline diagram where the
  client can draw one, else a text strip like `● ● ◉ ○ ○ ○ ○ ○  Step 3 of 8: the script`. Then one line on what this step
  is for.
- **Keep it very short.** Walls of text lose people. After the map: what you need from them now, as a short list.
  Findings go in a small table, never paragraphs. Detail only when they ask.
- **Reviews and results: five lines at most.** Any review, check or result is: what is good (one line), what is wrong
  (at most three short rows), one question. No reasons, causes or history unless asked. Explaining too much throws the
  person off and makes the reply more work than the video.
- **Always ask the step 2 questions.** Who it is for, what they should get from it, and how long it is are the person's
  decisions, even when a script seems to answer them. You may offer your guess as a default to confirm ("Developers
  doing large uploads? Yes / no"), but ask; never fill these in silently.
- **Never ask about the camera, the B-roll or the transitions.** The skills decide those; the person sees and can change
  them in the script at step 4. **Always ask the editing style** (step 5).
- **Ask in one message, then wait.** Group a step's questions; never drip them one per turn.
- **Show the script, inline, every time it changes.** With a one-line key above it (plain lines are spoken, `[ ]` lines
  are directions, `<!-- -->` lines are never spoken). Save it to a file as well.

The other skills live beside this one in `~/.claude/skills/` (in the suite repo under `skills/`). The script library is
a guide, not a skill: `~/.claude/skills/technical-video-script-library/`, or the repo's
`skills/technical-video-script-library/`.

## Step 1 of 8: what do you have?

A video needs a script and a raw recording of the person reading it; nothing can be built without the recording. Ask
both, every time, in one message:

> 1. Do you have a script? (Or notes, a docs page, an idea.)
> 2. Do you have the raw recording: the full, unedited file from Zoom or your camera, retakes and all?

Then say which path they are on, in one line:

| they have | path |
|---|---|
| script and raw recording | review, approve, build (the fastest) |
| script, no recording | review and approve, then they record (step 6), so they read the final words |
| idea, notes or a docs page | write the script with them, approve, then they record |

If they already said, give the step its map and the one-line path and go on. Check that any recording is a raw take.
Signs of an edit instead: a cut list beside it, a length close to the script's, black bars, a mirrored picture. The
build cuts and mirrors the take itself, so an edited file comes out cut twice; ask for the raw, full recording.

## Step 2 of 8: who is it for, and what should it do?

The questions that shape everything after. Ask them all, in one message, every time (offer a guess where the material
suggests one). Reasons are in the script library's `Audience and Purpose.md`:

1. **What are you trying to do with this video?** Teach a task, help someone choose, explain how something works?
2. **Who is it for?** Developers, a marketing or product team, customers, people new to Qdrant?
3. **What do they already know** about this?
4. **What should they do after watching?** Try it, choose an option, read more, get in touch?
5. **How long** should it be? A short (under a minute), about 3 minutes, 5 to 7 minutes?
6. **What supports this?** Links to anything that already covers it: the docs page, an article or blog post, a GitHub
   repo, a demo, a talk. The B-roll, the figures and the code on screen come from these, so nobody has to search for
   them later. If they have nothing, say you will look and propose some in step 3.
7. **Your name and title** for the name card (show it from memory for a yes: a misspelled name is the most visible
   mistake a video can have).

If they have nothing written, also ask them to tell you, in their own words, what they want to teach: a few sentences,
notes, a link or a voice memo. No structure needed yet.

Then recommend **one** of the ten structures in the script library's `README.md`, with one reason, following
`Recommendation Guide.md`. If a recording already exists and will be used, name the structure it follows instead.

## Step 3 of 8: the script, for that viewer

**If they have a script: review it against the step 2 answers.** Read it in full and fill in a small table:

| check | what to look at |
|---|---|
| Right viewer | Is every term this viewer would not know explained or shown? Is anything over-explained for an experienced viewer? |
| Right goal | Does the hook name the viewer's task? Does each section move toward the goal from step 2? |
| Right length | Spoken words against the target, at about 150 a minute. Say what to cut or add. |
| Right ending | Does the close resolve what the hook promised, then ask for the step 2 next step? |
| Sources | Each section of the script against the step 2 sources: which source, and which part of it, backs that section. A section with none is flagged: propose a source (search qdrant.tech docs, articles and blog), or keep that section on the presenter. |
| Correct | Code and claims against those sources as they are today (fetch them). Old syntax, numbers the sources do not give. |
| Ready to build | The suite's form ([references/script-form.md](references/script-form.md)): name card, source note, section times, directions. Missing pieces are filled in, not asked about. |

Run the B-roll and camera passes quietly; their results go into the script, not into questions. The key-term pass reads
one page at a time, so run it once per source and keep, for each line, the best match across them:
`python ~/.claude/skills/broll-recorder/scripts/keyterms.py SCRIPT.md SOURCE_URL --out keyterms.md` and
`python ~/.claude/skills/camera-layout/scripts/camera_plan.py SCRIPT.md --out camera_plan.md`.
When a recording will be used, compare its words with the script's and keep what was said: changes then go only into
what is shown (code, cards), never into the spoken lines, unless they will re-record.

**If they are starting from scratch: write it** in the recommended structure (its page under `Styles/` says what each
section does), for the viewer, goal and length from step 2, built from the step 2 sources. Show the same sources table:
each section and what backs it.

Either way, go straight on to step 4 with the script in hand.

## Step 4 of 8: approve the script

Show the whole script inline in the suite's form ([references/script-form.md](references/script-form.md)), all three
layers filled in by the skills:

1. **The lines**, for the viewer and the goal.
2. **The B-roll**: only lines that name something specific the docs page shows (broll-recorder's key-term rule).
3. **The camera calls and transitions** (camera-layout, transitions; Qdrant house rule: soft 0.8 s into and out of
   cards, code with a small top-right window).

Plus the name card after the first line and the source-page note at the top. Above it: the review table from step 3
(or, for a new script, one line per step 2 answer showing how the script meets it), and a short list of what changed.
Save it next to their files. Ask for approval; make every change they ask for in the script and show it again.

## Step 5 of 8: pick an editing style

Always ask. Default to Listed Sections if they have no preference:

| style | what it looks like | note |
|---|---|---|
| Listed Sections | the video as a numbered list, current item lit, the docs page's own figures and code | builds itself; needs docs sections with a "Best fit" line, or the screen stays empty (say so) |
| Animated Board | one board per section that builds as they speak; five looks | planned by hand for this video, takes longer |
| Code Report | fast and visual: real docs with highlights, captions, title cards | planned by hand for this video, takes longer |

The style pages are in the suite repo under `styles/`.

## Step 6 of 8: record, or hand over the take

If there is no recording yet:

- Read the approved script. Retakes and stumbles are fine: the editing skill keeps the last complete take of each line.
- Look at the lens; when the eyes leave it, the face goes off screen in the edit.
- Any webcam or Zoom recording works.

Then ask where the file is. A take recorded from a different version of the script lists the lines never said as NO TAKE
FOUND.

## Step 7 of 8: build, in three short checks

Hand over to **video-builder**; everything its "Ask first" section needs is answered by now. Nobody should wait an hour
and a half to find out something is wrong, so the build goes in three pieces, each shown and approved before the next.
Run every build in the background, with a one-line update as each stage finishes (from `BUILD_DIR/build.json`). A
failed stage stops the build and the command exits 1; `BUILD.md` and the stage's log say why.

**7a. The raw edit (a few minutes).** Cut only the take, and get it approved before anything is laid on it:

```bash
python ~/.claude/skills/video-builder/scripts/build.py --take RAW.mp4 --script SCRIPT.md --out BUILD_DIR --label "Topic, style" --style list --only cut
```

Show `BUILD_DIR/cut/cut.mp4` and a short table from `cut/cutlist.md`: which take of each line was kept, the lines with no
take, and where the words said differ from the script. Ask whether the cut is right. A wrong take or a clipped word is
fixed in the cut (editing skill) and cut again; nothing else has been built yet, so this is cheap.

Then the look-aways: run `--only words`, then `--only gaze`, and match `lookaways.json` to the script's lines. Presenters
look at their notes; that is fine, but the script must say what is on screen instead. Every line with a look-away over
about a second whose camera call shows the face full screen gets a new call: a small window and what stays up (the code,
the card, the B-roll, the list). Shorter glances are hidden by the engine on its own. Show the person one line per
change, not the whole script, and get a yes.

**7b. A preview (a few minutes).** Ask:

> Preview the first 30 seconds (a few minutes), or build the whole video?

Default to the preview. With Listed Sections use `--preview 60`: its first 30 s are mostly the presenter by design (the
list, code and trade-off cards start at the first item), so a 30 s preview shows almost no visuals. It builds into its
own folder:

```bash
python ~/.claude/skills/video-builder/scripts/build.py --take RAW.mp4 --script SCRIPT.md --out BUILD_DIR_preview --label "Topic, style" --style list --preview 30
```

Show it and ask whether the direction is right. A change of direction goes into the script (step 4) and the preview
runs again.

**7c. The whole video.** Once the cut and the direction are approved, continue the same build from the cut:

```bash
python ~/.claude/skills/video-builder/scripts/build.py --take RAW.mp4 --script SCRIPT.md --out BUILD_DIR --label "Topic, style" --style list --from words
```

## Step 8 of 8: small edits, until it is ready

The goal now is small fixes, not a new video. Never rebuild the whole thing for a small change.

1. **Check it.** Follow video-builder's "After the build": read `review/report.md`, look at the sheet and every fix
   frame, separate real faults from false alarms. Show the person a short numbered list of what is worth fixing, each
   with its time, and ask them to watch the video and add their own notes to the list.
2. **Fix in one batch.** Put each fix where it belongs (most go into the script's directions; a wrong take goes to the
   cut), then re-render only the seconds each one touches:

   ```bash
   python ~/.claude/skills/video-builder/scripts/build.py --take RAW.mp4 --script SCRIPT.md --out BUILD_DIR --label "Topic, style" --style list --patch T0 T1
   ```

   It grows the range to whole shots, splices it in, masters again, and writes `patch_T0-T1.mp4`: just that moment,
   with a second either side. A fix in the cut itself, the B-roll recordings or the spoken lines changes what comes
   after it, so those re-run from their stage (`--from STAGE --redo STAGE`) instead.
3. **Show only what changed.** Send the `patch_*.mp4` clips, not the whole video, and ask if each is right.
4. **Repeat** 2 and 3 until the list is empty. If the person does not like the video as a whole, that is not a small
   edit: go back to step 4 or 5.
5. **Final check.** When they are happy, run the full review once more (`--only review --redo review`), show the short
   result, and ask: **ready to go?** A yes is the end; the video is `BUILD_DIR/video_master.mp4`.

A fault the person finds that the review missed becomes a new review check with a self-test case (video-review).

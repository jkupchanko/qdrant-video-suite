# Qdrant video suite

Skills that take a technical video from idea to edit with less hand work.
Write the script, plan the camera layout, record selected supporting scenes, then edit.
The script leads the full sequence; each available skill also works on its own.

## Choose a part of the video

Choose a skill below. New parts of the suite are marked Coming soon.

<table>
<tr>
<td width="33%" valign="top">
<h3><a href="skills/technical-video-script-library/">Script writing</a></h3>
<p>Choose the viewer, hook, story structure and clean script layout.</p>
<p><strong>Available guide</strong></p>
</td>
<td width="33%" valign="top">
<h3><a href="skills/broll-recorder/">B roll</a></h3>
<p>Capture selected supporting scenes where they help explain the subject.</p>
<p><strong>Available skill</strong></p>
</td>
<td width="33%" valign="top">
<h3>Qdrant brand consistency</h3>
<p>Keep logos, colors and fonts aligned with the <a href="skills/broll-recorder/references/styles.md">existing production style</a>.</p>
<p><strong>Coming soon</strong></p>
</td>
</tr>
<tr>
<td width="33%" valign="top">
<h3><a href="skills/editing/">Editing</a></h3>
<p>Hand over the raw take and the script; get back the clean cut, the good take of every line, eyes on the lens, with a cut list of every decision.</p>
<p><strong>Available skill</strong></p>
</td>
<td width="33%" valign="top">
<h3><a href="skills/transitions/">Transitions</a></h3>
<p>How the picture gets from one shot to the next, measured from 50 watched videos: cut, one push, one flash.</p>
<p><strong>Available skill</strong></p>
</td>
<td width="33%" valign="top">
<h3><a href="skills/camera-layout/">Camera layout</a></h3>
<p>Plan face appearances, presenter size and consistent screen placement.</p>
<p><strong>Available skill</strong></p>
</td>
</tr>
<tr>
<td width="33%" valign="top">
<h3>Visual explanations</h3>
<p>Use diagrams, highlights and animation where the explanation needs them.</p>
<p><strong>Coming soon</strong></p>
</td>
<td width="33%" valign="top">
<h3>Audio and captions</h3>
<p>Keep speech clear, music restrained and captions readable.</p>
<p><strong>Coming soon</strong></p>
</td>
<td width="33%" valign="top">
<h3><a href="skills/video-review/">Final review</a></h3>
<p>Watch the finished video frame by frame and report every problem with its time and frame: the face, the text, the B-roll, the script, the sound.</p>
<p><strong>Available skill</strong></p>
</td>
</tr>
<tr>
<td width="33%" valign="top">
<h3><a href="skills/video-builder/">Build the whole video</a></h3>
<p>One request: the raw take and the script in, every skill in order, the finished video out with its review.</p>
<p><strong>Available skill</strong></p>
</td>
<td width="33%" valign="top">
<h3><a href="styles/">Editing styles</a></h3>
<p>Finished looks for the cut: Animated Board, Code Report, and Listed Sections, which builds itself from the script and the docs.</p>
<p><strong>Available</strong></p>
</td>
<td width="33%" valign="top">
</td>
</tr>
</table>

## 1. Script writing: [technical-video-script-library](skills/technical-video-script-library/)

Ten storytelling structures (the journey, the lesson, the practical tip, the comparison, and so on), a guide
for picking the viewer and the structure, and worked examples. Only selected supporting scenes need B roll.
Hand-off convention: the script marks each selected capture inline as
`[B-ROLL: URL | the line said there]` (syntax in `skills/broll-recorder/references/script-markers.md`). The
script skill is still being worked on; adding that marker to its output is the next step.

Defaults it helps with (each a small section inside the skill):

- choosing the viewer, their experience and funnel stage before the structure
- picking one of the ten structures from the viewer's question
- presentation and editing layout: where the hook, the proof and the follow-up go
- where B-roll belongs, and how to mark it

This folder is a subtree of the standalone repo `jkupchanko/technical-video-script-library`. Pull its latest
pushes in with:

```bash
git subtree pull --prefix skills/technical-video-script-library https://github.com/jkupchanko/technical-video-script-library.git main --squash
```

and push edits made here back out with `git subtree push` to the same prefix and remote.

## 2. Camera layout: [camera-layout](skills/camera-layout/)

The script determines what the viewer needs to see.
This skill plans presenter framing, inset size, content only views and split screen choices at the relevant passages.
It includes rectangular placeholder examples, a five minute camera plan and a review of thirty videos through ninety saved frame samples.
The full screen appearance count comes from the chosen sequence, rather than a fixed quota.
A measured audit of 32 popular AI and software-development videos (sampled every two seconds, 16 transcribed) backs the checks: opening hold, how fast the face returns, changes per minute, three layouts per video.
Hand-off from the script: a `[**Camera:** LAYOUT, position, size.]` line under the passage where the camera changes, required at the opening, wherever something must be read, wherever the person carries the line, at a section boundary, and at the close (`skills/camera-layout/references/camera-markers.md`).

## 3. B-roll: [broll-recorder](skills/broll-recorder/)

Trigger word: **B-roll**. Say what to show and get a finished 1080p60 clip in one consistent look: docs
zooms, article slides, code typing itself, title cards, and click-through flows done by the tool in a real
browser. Reads the `[B-ROLL: ...]` markers from step 1 and records them all in one run. Nothing to install
beyond a one-time `setup.py`.

Demo: `demos/broll_skill_pitch.mp4` (77 s).

## 4. Transitions: [transitions](skills/transitions/)

How the picture gets from one shot to the next, measured from the same 50 videos: 62% of visible changes
are labels and cards over a held shot, and among real shot changes 65% are cuts. Rules, taken only from what the
eight most-watched presenter-plus-screen videos do: cut by default, a 0.3 s push only for a card arriving
over the presenter, a white flash only at a chapter break; dissolves, black fades and punch-ins were not
seen there and are not used. Audits any video, renders the same join several ways on real footage, and
writes the choice into the script's Transition field.

## 5. Editing: [editing](skills/editing/)

The raw take and the script in, a clean cut out. Transcribes the recording, finds every take of every line
and keeps the last complete one, checks eye contact on each, cuts on word boundaries, mirrors, covers the
recording tag with matching bars, alternates a slight push between cuts, and writes a cut list of every
decision. The camera calls, B-roll and transitions are laid onto this cut.

## 6. Assemble

Drop the clips into the timeline. More skills for this step will be added here as they are ready.

## 7. Review: [video-review](skills/video-review/)

The last step, and the one that decides whether a video is ready. It watches the render, not the plan: the face on screen
while the eyes are off the lens, a stretched face or a head cut off by its window, lip sync, text cut at the edge or spilling
out of its card, tiny text, typos, numbers nobody gave, outdated API spellings, B-roll that is missing, late or on the wrong
section, lines the cut lost, empty or frozen frames, loudness. Each finding comes with its frame. A self-test plants four
faults in a real clip and fails if one is missed.

## 8. The whole video in one request: [video-builder](skills/video-builder/)

`build.py --take RAW.mp4 --script SCRIPT.md` runs every skill above in order and ends with the review. Built from the raw
Bulk Uploads take, the first build's review found the six lines the cut had dropped and the B-roll lost with them; each fix
went into the skill that caused it, and the next build came back clean.

## A finished example, every skill applied

`demos/bulk-uploads-first30/`: the first 30 seconds of the Bulk Uploads video from a raw Zoom take.
`face_only_720.mp4` is the edit on its own (takes chosen by transcript, eye contact checked, mirrored, bars,
push between cuts); `suite_720.mp4` adds the camera calls, the docs B-roll and the transitions. The script
with the calls, the cut list and the key-term B-roll pass sit beside them.

## Reviewing

This is open for review and use. Read the README in each skill folder, try the commands, and open an issue
or a pull request with what broke or what you would change. MIT licensed.

## Using a skill with Claude

Copy the skill folder into `~/.claude/skills/` (or point Claude Code at it) and ask in plain words. The
SKILL.md or README.md in each folder is what Claude follows.

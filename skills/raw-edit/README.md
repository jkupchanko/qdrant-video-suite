# Raw edit

**Your full recording and your script in; one clean pass out.**

You record the way you record now: retakes, restarts, pauses to think, a glance at your notes. This skill cuts it into
one clean flow, where each thought is said once, in whole sentences, while you look at the viewer. It finds the faults
a careful editor would catch, fixes them itself, and gives you a page to check the result by clicking.

![How the raw edit is made](images/how-it-works.png)

## What it fixes

Four faults, the ones presenters kept spotting by hand. Each is shown on a real take below: red comes out, blue goes back in.

![The four faults on a real take](images/four-faults.png)

1. **Said twice.** You started a sentence, stopped and said it again. The first try comes out.
2. **A stop mid-sentence.** A long silence where the sentence goes on. It is cut down to a natural pause.
3. **A glance at a cut.** You stopped mid-thought and looked away to think. The piece ends on the word, before your eyes move.
4. **Words left out.** Part of your script line was said but fell between two pieces. It goes back in.

## Measured on you

Everyone pauses and looks away differently, so there is no fixed number. Before checking, the skill measures your own
take: your usual pause inside a sentence, how loud your room and voice are, and where your eyes rest when you look at
the lens. A fast talker's 0.4 s silence is a stop; a slow talker's is a breath.

Every limit was checked against 49 popular technical videos, measured the same way. Pros pause anywhere from 0.12 to
0.28 s inside a sentence, glance away briefly 14 times a minute, and their finished videos pass these checks: a fix is
only made where it is sure, and anything that might be said on purpose is shown to you instead. The reason for each
rule: [references/rules.md](references/rules.md). The numbers: [references/research.md](references/research.md).

![Checked against 49 popular technical videos](images/research.png)

## Review it by clicking

Every build writes `review.html` next to the cut. Click a time to jump there, mark it **Fine** or **Fix**, and press
**M** wherever something is off that nothing flagged. **Save notes**, and the fixes go in.

![The review page](images/review-page.png)

## Use it

It runs as the first step of every build (`build.py --only cut` makes just the raw edit). To look at or fix one moment:

```bash
python ~/.claude/skills/raw-edit/scripts/fix_cut.py BUILD/cut RAW.mp4 --at 2:33
python ~/.claude/skills/raw-edit/scripts/fix_cut.py BUILD/cut RAW.mp4 --notes review_notes.json
```

Or just tell Claude: "at 2:33 I look away and it cuts me off".

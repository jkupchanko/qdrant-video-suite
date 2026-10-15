# Editing rules

The rules a cut follows, learned from editing a full raw Zoom take of a scripted video into a finished
face-only cut. They are how the tool behaves; when cutting by hand, follow the same rules.

## Choosing the take

1. **The last complete take wins.** A presenter restarts until a line is right, so the last take that
   says the whole line is the keeper. Earlier stumbles, half-lines and false starts are dropped.
2. **Retakes sit close together.** A line said again within about 45 seconds is a retake of the same
   line. The same words said minutes later are a different moment in the video and do not compete.
3. **A restart replaces its stumble.** "Because they're different, because they're different, they
   create..." becomes one clean line from the second start.
4. **Half-takes can be joined.** When the presenter gets the first half right and restarts only the
   second half ("...it reduces your RAM usage, especially as your sparse... Especially as your sparse
   index starts to grow."), use the first half of one take and the restart of the second half.
5. **Spoken wording wins over the script.** If the presenter said it differently and it is correct, keep
   what was said; the cut list records the difference so the writer can decide.
6. **Lines that are not in the script go**: ad-libs ("because of this"), extra calls to action, a second
   sign-off. The script decides what the video says.

## Eyes on the lens

7. **The presenter looks at the lens whenever they talk.** Every chosen take is checked frame by frame.
   A take under 80% eye contact is flagged for a person to look at; it is never swapped quietly.
8. **The only exception** is a passage where the script has the presenter look at something on screen.

## Where a cut goes

9. **In-point: just before the first word**, about 0.08 s. Never on a breath.
10. **Out-point: where the voice actually stops, plus a quarter second of air.** The transcript marks a
    word as finished slightly before the sound stops; cutting on that mark clips the end of the line.
    The tool finds the real end of speech from the audio.
11. **Never into the next word.** The out-point stops short of the next spoken word, whatever the air rule says.
12. **Pauses inside a take are removed.** Any silence longer than 0.7 s inside a line is cut out, keeping a
    quarter second of air on each side so the speech does not sound chopped. Long thinking pauses mid-line
    ("Uploading points... one at a time") disappear.
13. **A soft final consonant is not silence.** Silence is measured at -42 dB so trailing sounds survive.

## The picture and the sound

14. **Mirror the webcam image** so the presenter faces the way they do in life.
15. **Hide a recording tag** (the Zoom name label) with a black bar at the bottom and a matching bar at the
    top, so it reads as a deliberate frame rather than a patch. 72 px at 1080p covers the Zoom label.
16. **Alternate a slight push between cuts** (1.00 and 1.06) so each jump between takes reads as a cut, not
    a glitch.
17. **Fade the audio 20 ms at every join.** No clicks.
18. **Nothing else is added** in the edit: no music, labels, B-roll or transitions. Those come from the other
    skills and are laid onto this cut.

## Checking before it ships

19. **Read the cut list.** It lists every line, the take used, what was actually said, and the eye-contact
    score. The automatic take-matching gets most lines right but not all: on a full nine-minute take it
    missed two lines, matched a title that was never spoken, and started two lines mid-sentence. A person
    reads the cut list and corrects those before the cut is final.
20. **Check that no piece ends while the voice is still going.** The last tenth of a second of each piece
    should be quiet unless it flows straight into the next piece in the original recording.
21. **Work in small amounts.** Cut and review 30 seconds first; when that is right, do the rest the same way.

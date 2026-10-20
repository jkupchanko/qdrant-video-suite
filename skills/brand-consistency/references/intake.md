# Intake: the questions before a build

A build makes many choices on its own (which take, which layout, when the B-roll lands). A few answers it cannot make,
because only the presenter knows them, and getting them wrong shows on screen. Ask these first, in one message, and wait.

| question | why it matters | what happens with the answer |
|---|---|---|
| Your name, as it should read on the name card? | The name card is on every Qdrant video; a misspelled name is the most visible mistake a video can have. | Goes into the script as `[**Lower third:** NAME \| TITLE \| 5 s]` (or `build.py --name`). The review checks the screen against this spelling. |
| Your title under it? | Same card; titles change, and a guessed one is wrong. | Same directive (`--role`). |
| Where is the raw take? | Nothing replaces the recording. | `--take`. If there is none, stop and say so. |
| Is there a script, three-layer form? | The script controls the video: lines, B-roll, camera calls, transitions, the name card. | `--script`. If there is only a topic, write the script first and show it inline (script + camera calls + transitions) before building. |
| Which docs page is it about? | The B-roll, the figures, the code and the tradeoff chips all come from it. | The script's `Source page:` note, or `--url`. |
| Which style? | Listed sections builds itself; Code Report and Animated Board are planned by hand per video. | `--style list` (default). |

When the person has already given an answer (in this conversation, in the script, or in memory), do not ask it again:
say what you are using ("name card: John Kupchanko, Developer Relations Engineer, from the script") and go on.

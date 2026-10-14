# Stop Uploading Points One at a Time

Three minutes. Camera written in by the camera skill: a `[**Camera:** ...]` line wherever the camera
changes; between lines it holds. Window = small rectangle, 4:3, 20% of frame width, top right, 24 px in,
corner checked against each card so nothing sits under it. The planner's first pass is in
`script-planner-pass.md`; this is the pass after reading it against the script.

## Hook   0:00 to 0:15

**Written hook:** One call. All your points.

**Verbal hook**

If you are loading a dataset into Qdrant with a for loop and an upsert inside it, this is the one change to make before you run it again.
It takes one line, and you can see the difference in the terminal.

[**Camera:** FULL, centred. Holds through the hook; the written hook sits over the shoulder. **Show:** The written hook. **Transition:** Cut to the checklist.]

## Before you change it   0:15 to 0:40

You need three things already in place.
A collection that exists, with the vector size your embeddings use.
A list of points, each with an id, a vector and whatever payload you want to filter on later.
And the Python client connected to your cluster.

If those are there, the rest is one call.

[**Camera:** SMALL, top right, 20%. A three-line checklist is light; presence stays. Top right of the card is clear. **Show:** The three items as a checklist beside the connected client. **Transition:** Keep the checklist visible as the code appears.]

## The change   0:40 to 2:00

Here is the loop most people start with.
It calls upsert once per point.
Every call is a round trip to the server, so a hundred thousand points means a hundred thousand round trips.

[**Camera:** SMALL, top right, 20%, unchanged. New section, same window: code gets the small window by house rule, and the code card is clear in that corner. **Show:** The loop, upsert line highlighted. **Transition:** Slide the loop up to make room for the replacement.]

Replace the loop with upload_points.
Give it the collection name and the list of points.
Set batch_size to something like two hundred and fifty six.

[**Show:** The upload_points call, batch_size highlighted. Same window. **Transition:** Hold on the call.]

The client now groups the points into batches of that size and sends each batch as one request.
Nothing about your points changes.
Only how many trips they take.

[**Camera:** FULL. The explanation of what changed and what did not is the person's; the face has been small for about 65 s. **Transition:** Cut to the docs insert.]

[**Camera:** NONE for the insert (implied by the B-roll block). **Show:** The docs page, "Upload Points", batch_size parameter in view.]

[**B-ROLL: https://qdrant.tech/documentation/concepts/points/ | upload points in batches | 6s]

Run both versions on the same list and print the elapsed time after each.
Read the two numbers you get.

[**Camera:** NONE. The terminal output runs the full width and the two times are the point of focus; no corner is clear. **Show:** The terminal with both runs and their elapsed times. **Transition:** Hold on the two numbers.]

The batched one is the one to keep.

[**Camera:** FULL. The verdict is the person's line. **Transition:** Cut to the dashboard.]

## How you know it worked   2:00 to 2:40

Open the collection in the dashboard and read the point count.
It should match the length of your list.
If it is short, the upload stopped partway; the client prints the batch it failed on, so start again from there.

One condition changes how useful this is.
If your points carry large payloads, a smaller batch size keeps each request inside the server's limits.
Try two hundred and fifty six first, and halve it if you see request size errors.

[**Camera:** SMALL, 20%. Corner checked against the dashboard capture: the collection header sits top right, so the window goes top left for this section and stays there. **Show:** The dashboard point count beside the length of the list, then the batch_size line. **Transition:** Return to the opening loop.]

## Try it on yours   2:40 to 3:00

Take the loop you have, swap the loop for one upload_points call, and run it on the same data.
Read the elapsed time and the point count.

[**Camera:** SMALL, top right, 20%. New section, back to the house corner; the card is clear there. **Show:** The one call, then the two checks as a short card.]

That is the whole change.

[**Camera:** FULL. Close on the person. **Transition:** End card.]

## Count

Layouts: FULL, SMALL, NONE. Camera lines: 10 in three minutes, about 3 changes a minute. Longest stretch
without the full face: 65 s (0:15 to 1:20), with the small window on for all of it. Longest with no face at
all: 17 s (the insert and the terminal). Window corner: top right, except the dashboard section, where the
check moved it to top left for that section only.

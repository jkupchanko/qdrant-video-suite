# Stop Uploading Points One at a Time

## Hook   0:00 to 0:15

**Written hook:** One call. All your points.

**Verbal hook**

If you are loading a dataset into Qdrant with a for loop and an upsert inside it, this is the one change to make before you run it again.
It takes one line, and you can see the difference in the terminal.

[**Show:** The for loop with the upsert inside it, then the terminal with its elapsed time. **Transition:** Cut to what you need before changing it.]

## Before you change it   0:15 to 0:40

You need three things already in place.
A collection that exists, with the vector size your embeddings use.
A list of points, each with an id, a vector and whatever payload you want to filter on later.
And the Python client connected to your cluster.

If those are there, the rest is one call.

[**Show:** The three items as a short checklist beside the connected client. **Transition:** Keep the checklist visible as the code appears.]

## The change   0:40 to 2:00

Here is the loop most people start with.
It calls upsert once per point.
Every call is a round trip to the server, so a hundred thousand points means a hundred thousand round trips.

[**Show:** The loop, with the upsert line highlighted. **Transition:** Slide the loop up to make room for the replacement.]

Replace the loop with upload_points.
Give it the collection name and the list of points.
Set batch_size to something like two hundred and fifty six.

The client now groups the points into batches of that size and sends each batch as one request.
Nothing about your points changes.
Only how many trips they take.

[**Show:** The upload_points call, batch_size highlighted. **Transition:** Run it.]

[**B-ROLL: https://qdrant.tech/documentation/concepts/points/ | upload points in batches | 6s]

Run both versions on the same list and print the elapsed time after each.
Read the two numbers you get.
The batched one is the one to keep.

[**Show:** The terminal with both runs and their elapsed times. **Transition:** Cut to the check.]

## How you know it worked   2:00 to 2:40

Open the collection in the dashboard and read the point count.
It should match the length of your list.
If it is short, the upload stopped partway; the client prints the batch it failed on, so start again from there.

One condition changes how useful this is.
If your points carry large payloads, a smaller batch size keeps each request inside the server's limits.
Try two hundred and fifty six first, and halve it if you see request size errors.

[**Show:** The dashboard point count beside the length of the list, then the batch_size line. **Transition:** Return to the opening loop.]

## Try it on yours   2:40 to 3:00

Take the loop you have, swap the loop for one upload_points call, and run it on the same data.
Read the elapsed time and the point count.
That is the whole change.

[**Show:** The one call, then the two checks as a short card. **Transition:** Finish on the card.]

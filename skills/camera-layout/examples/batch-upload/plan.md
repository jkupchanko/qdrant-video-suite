# Camera plan: Stop Uploading Points One at a Time

3.0 min, 2.0 changes a minute, 2 layouts carrying 5%+ of the time. Shares: full 43%, small 57%.

| time | section | says | layout | size and position | hold | why |
|---|---|---|---|---|---|---|
| 0:00 | Hook | If you are loading a dataset into Qdrant with a for loop and an upsert... | **full** | head and shoulders, centred | 15 s | hook: the person asks the question |
| 0:15 | Before you change it | You need three things already in place. A collection that exists, with... | **small** | window 20% width, corner (top-right) | 25 s | something is on screen but not dense: presence, small |
| 0:40 | The change | Here is the loop most people start with. It calls upsert once per poin... | **full** | head and shoulders, centred | 23 s | code on screen: house rule, small window top right so the person stays while they read (away from full for over 40 s: come back) |
| 1:03 | The change | Replace the loop with upload_points. Give it the collection name and t... | **small** | window 20% width, corner (top-right) | 38 s | code on screen: house rule, small window top right so the person stays while they read |
| 1:41 | The change | Run both versions on the same list and print the elapsed time after ea... | **full** | head and shoulders, centred | 19 s | code on screen: house rule, small window top right so the person stays while they read (away from full for over 40 s: come back) |
| 2:00 | How you know it worked | Open the collection in the dashboard and read the point count. It shou... | **small** | window 20% width, corner (top-right) | 40 s | walkthrough: presence while the viewer follows the cursor |
| 2:40 | Try it on yours | Take the loop you have, swap the loop for one upload_points call, and ... | **full** | head and shoulders, centred | 20 s | code on screen: house rule, small window top right so the person stays while they read (away from full for over 40 s: come back) |

## Checks

- opening hold, return-to-face, no-face stretch, variety and pace are all inside the corpus habits

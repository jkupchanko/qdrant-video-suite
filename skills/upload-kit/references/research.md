# What 49 popular technical videos put around the video

The same 49 popular AI and software-development videos the other skills were measured on. On 2026-10-28 their public
page data was fetched (`yt-dlp --skip-download --write-info-json --write-thumbnail`: no video downloaded) and measured
with `scripts/audit_upload.py`.

## What was measured

| measure | 49 pro videos | what it decided |
|---|---|---|
| title length | median 50 characters, 8 words; middle 80% 28 to 67 | check under 20 or over 70; fix over 100 (YouTube's limit) |
| title shape | split by a colon or dash 13/49, a question 5/49, a number 14/49, brackets 12/49, an emoji 0/49, a word in capitals 15/49 | no emoji; at most one word in capitals |
| description, first two lines | median 110 characters; a link in them 33/49 | the docs link in the first lines |
| description links | median 4; to docs or GitHub 15/49; hashtags 27/49; timestamps written 27/49 | every page the video shows, listed |
| chapters | 41/49; median 8 a video, about 65 s each, the shortest a median 29 s; titles of 3 or 4 words | one per script section, timed by the cut |
| thumbnail | 2 to 4 big words (OCR counts a median 6 with small print); a face on 30/49 (about a tenth of the frame); dark (median brightness 0.3) with one strong colour, red on 19/49 | not made by the suite yet (below) |

## The decisions, with the reason for each

1. **The chapters are the script's sections.** The person who wrote the script already chose what a viewer would look
   for. Each starts where the cut first says one of its lines, not where the script planned it: the cut is what plays.
   YouTube's own rules make a fix: the first at 0:00, three or more, 10 s or more each. A section the cut leaves under
   10 s joins the next with both titles kept, so no topic falls off the list. (A first rule merged sections under 20 s
   into the one before: on Get Started it showed "Intro" until 1:01, over the Docker part. Titles must not disappear.)
2. **The description leads with the hook and what the viewer gets.** The intro's opening line, then its "by the end,
   you'll have..." line (or its "you can..." line), never "I'll show you"; then the source page as a link, which is
   where 33 of 49 put one. (Picking only the "you can" line opened the Bulk Uploads demo with "So we will go over a few
   different options and best practices you can try.")
3. **The title is the person's choice.** The script's title is the draft; Claude proposes three by the numbers above
   and the person picks. A title is a judgement about the audience, not a measurement.
4. **No thumbnail yet.** The 49 show what works (big words, a face or a logo, one strong colour), and three directions
   were sketched for Get Started. John, 2026-10-28: wait; a thumbnail that is right is more work than a template. Made
   by hand until it is done properly.

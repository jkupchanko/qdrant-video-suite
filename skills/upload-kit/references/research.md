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

# Titles: 19,463 from 63 technical channels

The 49 above say how long a title runs, not which wording does well. On 2026-10-28 `scripts/title_study.py` fetched the
newest ~400 uploads of 63 channels (page data only, Shorts left out) in three groups: educators (Fireship, freeCodeCamp,
TechWorld with Nana, ByteByteGo, Traversy, ...), AI builders (James Briggs, Dave Ebbelaar, Sam Witteveen, Cole Medin,
...) and the DevRel channels of developer companies (MongoDB, Docker, AWS Developers, Redis, Supabase, Pinecone,
Weaviate, Elastic, Neon, Postman, GitHub, Qdrant, ...). Qdrant's videos are DevRel videos, so that group decides.

**How a feature is judged.** A video's lift is its views against the median of its 30 nearest uploads on the same
channel: the neighbours share the channel's size and the video's age, so a big channel or an old upload does not win by
being big or old. A feature's effect is the median, across channels that use it at least 6 times and leave it out at
least 6 times, of the difference in median lift, as a multiple of views; the 90% range comes from resampling channels.

| on DevRel channels | views vs. titles without it | channels where it helps |
|---|---|---|
| Explained / What is ... | 2.4x / 2.3x | 100% / 100% |
| Getting Started (all channels; on DevRel 2.3x, range crossing 1x) | 2.3x | 80% |
| a time ("in 5 minutes") | 2.3x | 90% |
| Guide | 2.1x | 86% |
| vs | 1.9x | 100% |
| for Beginners (all channels) | 2.2x | 93% |
| a question / opens with How to | 1.6x / 1.5x | 79% / 81% |
| under 30 / 30 to 49 characters | 1.35x / 1.22x | 81% / 79% |
| names a product or tool | 1.19x | 74% |
| a colon / a number / a word in capitals | 0.84x / 0.84x / 0.86x | 35% / 35% / 35% |
| a part or episode number | 0.74x | 38% |
| the year | 0.76x | 21% |
| an event name (Conf, Summit, keynote) | 0.69x | 33% |
| 70 characters or more | 0.74x | 8% |

The DevRel tutorials that beat their neighbours most read like a task and a tool: "How to containerize Python
applications with Docker", "Getting Started with Docker", "Learn Drizzle ORM in 13 mins (crash course)", "How to Build
Your First MCP Server (in Less Than 5 Minutes)". The ones that trailed most name an event, a speaker or a part: "Pinecone
AWS Reference Architecture Deployment Part 3", "Opening keynote: ... at GitHub Universe 2026".

**What it decided.**

5. **Titles are scored, not generated.** `scripts/titles.py` multiplies the effects that held up (90% range clear of 1x;
   DevRel where measured, else all channels) into a score, and lists title ideas from the script in the shapes that led:
   Getting Started with ..., ... in N Minutes, ... for Beginners, ...: A Step-by-Step Guide, How to <task section>.
   Claude writes its own three, scores them with the ideas, and the person picks. The score ranks; it does not forecast:
   effects overlap (a "Getting Started" title is also short and names a tool), and the topic moves views far more than
   the wording.
6. **What trailed is checked**: 70+ characters, a year, a part or episode number, an event name, "live" or "webinar",
   no product named. Checks, not fixes: a series or a launch may need them.
7. **Only say what is true.** "In 5 minutes" only for a video that runs about 5 minutes; "for Beginners" only when the
   script assumes nothing. A title that wins the click and loses the viewer costs more than it gains.

Measured association, not cause: "Explained" and "Getting Started" also say what kind of video it is, and a channel's
evergreen explainers collect views for years. Rerun with `python title_study.py CORPUS_DIR --fetch` (yt-dlp needed); it
rewrites `references/title_effects.json`, which `titles.py` reads.

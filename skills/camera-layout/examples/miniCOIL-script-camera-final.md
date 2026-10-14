# Can Spanish Search Find an English Answer?

The five minute script with the camera written in. One `[**Camera:** ...]` line wherever the camera changes;
between lines it holds. Window = small rectangle, 4:3, 20% of frame width, top right, 24 px in, unless the
line says otherwise. The corner is checked against what is on screen (nothing under the window) and stays
put through a section.

## Hook   0:00 to 0:20

**Written hook:** Spanish question. English answer.

**Verbal hook**

Your search box accepts Spanish, but your documents are in English.
Can it still find the right answer?
Let's try it with three short passages and a little Python.

[**Camera:** FULL, centred. Holds through the hook. **Show:** The written hook over the presenter. **Transition:** Cut to the three passages.]

## Set up the example   0:20 to 0:50

One passage is about a dog running through a park.
One is about soup.
And one is about a star.

[**Camera:** SMALL, top right, 20%. The passages card has nothing in that corner. **Show:** The query and the three English passages, intended answer marked. **Transition:** Keep the query visible.]

Our first question is perro corriendo en el parque.
That means a dog running in the park.
We want the search to find the dog passage.

The collection and encoder are already prepared.
We're going to follow the question through the search and inspect what comes back.

[**Camera:** FULL. "We want the search to find" and "we're going to follow" are the person's lines; nothing new to read. **Transition:** Cut to the concept card.]

## Explain the connection   0:50 to 1:35

Why would perro match dog?
They're different words, but they refer to the same thing.

[**Camera:** SMALL, top right, 20%. The perro / dog concept card is light; presence stays. **Show:** perro and dog over one shared concept. **Transition:** Hold the card for the article insert.]

This version of miniCOIL connects related English and Spanish words through a shared concept.
The article illustrates this with home and casa.
Both words contribute to the same part of the search representation.

[**Camera:** NONE for the insert. The figure is the point; the article page has a sidebar in the top right, so no window. **Show:** The article's home and casa illustration, cropped so the words and the shared slot are readable.]

[**B roll:** **Find:** [The article](https://qdrant.tech/articles/minicoil-en-es/), opening illustration beneath the introduction. **Capture:** A steady close view of the home and casa diagram. **Use during:** "The article illustrates this with home and casa."]

For each trained concept, the encoder produces eight numbers.
Those numbers also depend on the surrounding text.

[**Camera:** SMALL, top right, 20%. Back to the same corner as before the insert. **Show:** The eight slots under the concept, lit as the words change. **Transition:** Settle on the two matching slots.]

The question and passage can share a concept even though their words are in different languages.
That gives them a way to match without translating the question first.

[**Camera:** FULL. The "that gives them a way" line is the explanation; the face has been small or off for about 40 s. **Transition:** Cut to the encoding calls.]

## Show the code   1:35 to 2:35

Here's how that becomes a search.

We encode the passage as English.
Then we encode the question as Spanish.

Notice that we also mark the question as a query.
That matters because the encoder handles a question differently from a stored passage.

[**Camera:** SMALL, top right, 20%. House rule for code: the person stays while the viewer reads. The code card is clear in that corner. **Show:** The two encoding calls, language settings and is_query=True highlighted. **Transition:** Follow the passage into the prepared collection.]

The encoder returns positions and values for a sparse vector.
Sparse means we keep the positions with values instead of listing every empty position.

We store the passage's vector in Qdrant alongside its text.
This collection also uses the IDF setting, which weights positions according to how common they are across the collection.

[**Show:** The sparse vector configuration, Modifier.IDF highlighted. Same window, same corner. **Transition:** Move to the search call.]

Now we send the encoded question to the collection.
Let's see which passages come back.

[**Camera:** FULL. "Now" and "let's" turn the sentence; nothing to read; the hand-off to the results is the person's. **Transition:** Cut to the results.]

## Run the search   2:35 to 3:35

Here are the results.

Did the dog passage appear?
And where did it rank?

[**Camera:** NONE. Results are looked at, and the ranked list runs the full width, so no corner is clear. **Show:** The three returned passages with their ranks, the dog passage marked.]

That's our first check.
The question was in Spanish, and the passages were in English.

[**Camera:** FULL. The check summary is the person's line. **Transition:** Cut to the second query.]

Now let's try sopa con cebolla y ajo.
That means soup with onion and garlic.

This time, we want the soup passage.
We use the same process and inspect the result.

[**Camera:** NONE. Same reason as the first result. **Show:** The second query's results, soup passage marked.]

We've checked two questions against a tiny collection.
What happens when the words are the same across languages, but the meaning is not?

[**Camera:** FULL. The question that opens the next section. **Transition:** Cut to the bat card.]

## Explain the limit   3:35 to 4:20

Take the English word bat.
It could mean an animal or something you use in a game.

[**Camera:** SMALL, top right, 20%. The bat card is a single word with two meanings; light. **Show:** bat with its two meanings.]

Sharing a concept is only part of the task.
The surrounding words help decide which meaning applies.

[**Camera:** NONE for the insert. Article page again, sidebar top right. **Show:** The article's passage on bat and murcielago.]

[**B roll:** **Find:** [The article](https://qdrant.tech/articles/minicoil-en-es/), "Same Word, Different Language". **Capture:** The bat example with its two senses. **Use during:** "The surrounding words help decide which meaning applies."]

The released version also has a limited set of trained concepts.
Words outside that vocabulary fall back to exact matching.

So your own vocabulary belongs in the test.

[**Camera:** FULL. The limit, then the advice, are the person's. **Transition:** Cut to the practice card.]

## Give them something to try   4:20 to 5:00

Start with a few short English passages you can judge yourself.
Write three questions in Spanish.
Run each one and record where the intended passage ranks.

[**Camera:** SMALL, top right, 20%. The practice card is three lines; presence stays. **Show:** The three steps as a card.]

That's your first experiment.
A few passages, three questions, and results you can judge yourself.

[**Camera:** FULL. Close on the person. **Transition:** End card.]

## Count

Layouts: FULL, SMALL, NONE (three). Camera lines: 17 in five minutes. Window corner: top right throughout;
it goes to NONE rather than moving when the article page or the results would sit under it. The face is
never away for more than about 50 s, and comes back to FULL eight times, each on a line that is the
person's.

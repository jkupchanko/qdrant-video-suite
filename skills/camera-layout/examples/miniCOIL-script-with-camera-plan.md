# Can Spanish Search Find an English Answer?

## Hook   0:00 to 0:20

**Written hook:** Spanish question. English answer.

**Verbal hook**

Your search box accepts Spanish, but your documents are in English.  
Can it still find the right answer?  
Let’s try it with three short passages and a little Python.
> **Camera plan (0:00, 20 s):** FULL, head and shoulders, centred. hook: the person asks the question

[**Camera:** Centered medium shot for the opening question, then face hidden. **Show:** A Spanish query beside an English passage. **Transition:** Reveal the three passages we will search.]

## Set up the example   0:20 to 0:50

One passage is about a dog running through a park.  
One is about soup.  
And one is about a star.
> **Camera plan (0:20, 9 s):** SMALL, window 18% width, corner (bottom-right). something is on screen but not dense: presence, small

Our first question is perro corriendo en el parque.  
That means a dog running in the park.  
We want the search to find the dog passage.
> **Camera plan (0:29, 11 s):** FULL, head and shoulders, centred. opinion, reason or summary: the person carries it

[**Camera:** Small face in the top right, roughly 20% of the screen width. **Show:** The query and three English passages, with the intended answer marked. **Transition:** Keep the query visible.]

The collection and encoder are already prepared.  
We’re going to follow the question through the search and inspect what comes back.
> **Camera plan (0:40, 10 s):** FULL, head and shoulders, centred. explanation with nothing to read: the person carries it

## Explain the connection   0:50 to 1:35

Why would perro match dog?  
They’re different words, but they refer to the same thing.
> **Camera plan (0:50, 8 s):** NONE, screen only. the viewer must read what is on screen

This version of miniCOIL connects related English and Spanish words through a shared concept.  
The article illustrates this with home and casa.  
Both words contribute to the same part of the search representation.
> **Camera plan (0:58, 16 s):** NONE, screen only. the viewer must read what is on screen

[**Camera:** Hide the face during the article insert, then return to the same top right position. **Show:** The article’s home and casa illustration, cropped so the words and shared positions are readable. **Transition:** Return to our dog example.]

[**B roll:** **Find:** [The article](https://qdrant.tech/articles/minicoil-en-es/), opening illustration beneath the introduction. **Capture:** A steady close view of the home and casa diagram. **Use during:** “The article illustrates this with home and casa.”]

For each trained concept, the encoder produces eight numbers.  
Those numbers also depend on the surrounding text.
> **Camera plan (1:13, 8 s):** SMALL, window 18% width, corner (bottom-right). something is on screen but not dense: presence, small

The question and passage can share a concept even though their words are in different languages.  
That gives them a way to match without translating the question first.
> **Camera plan (1:22, 13 s):** FULL, head and shoulders, centred. something is on screen but not dense: presence, small (away from full for over 40 s: come back)

[**Camera:** Return to a centered medium shot for the final sentence. **Show:** The presenter explaining the connection. **Transition:** Cut to the encoding calls.]

## Show the code   1:35 to 2:35

Here’s how that becomes a search.
> **Camera plan (1:35, 4 s):** NONE, screen only. the viewer must read what is on screen

We encode the passage as English.  
Then we encode the question as Spanish.
> **Camera plan (1:39, 7 s):** NONE, screen only. the viewer must read what is on screen

Notice that we also mark the question as a query.  
That matters because the encoder handles a question differently from a stored passage.
> **Camera plan (1:46, 12 s):** NONE, screen only. the viewer must read what is on screen

[**Camera:** Face hidden throughout the code walkthrough. **Show:** The two encoding calls, with the language settings and is_query=True highlighted. **Transition:** Follow the passage into the prepared collection.]

The encoder returns positions and values for a sparse vector.  
Sparse means we keep the positions with values instead of listing every empty position.
> **Camera plan (1:58, 13 s):** NONE, screen only. the viewer must read what is on screen

We store the passage’s vector in Qdrant alongside its text.  
This collection also uses the IDF setting, which weights positions according to how common they are across the collection.
> **Camera plan (2:11, 16 s):** SMALL, window 18% width, corner (bottom-right). the viewer must read what is on screen (no face for over 50 s: bring in a small window)

[**Show:** The sparse vector configuration, with Modifier.IDF highlighted. **Transition:** Move to the search call.]

Now we send the encoded question to the collection.  
Let’s see which passages come back.
> **Camera plan (2:27, 8 s):** FULL, head and shoulders, centred. explanation with nothing to read: the person carries it

## Run the search   2:35 to 3:35

Here are the results.
> **Camera plan (2:35, 3 s):** NONE, screen only. the viewer must read what is on screen

Did the dog passage appear?  
And where did it rank?
> **Camera plan (2:38, 7 s):** NONE, screen only. the viewer must read what is on screen

That’s our first check.  
The question was in Spanish, and the passages we searched were in English.
> **Camera plan (2:45, 13 s):** NONE, screen only. the viewer must read what is on screen

[**Camera:** Face hidden while the results are inspected. **Show:** The actual results beside the intended answer. **Transition:** Keep the collection unchanged and replace the query.]

Now let’s try sopa con cebolla y ajo.  
That means soup with onion and garlic.
> **Camera plan (2:58, 11 s):** NONE, screen only. the viewer must read what is on screen

This time, we want the soup passage.  
We use the same process and inspect the results again.
> **Camera plan (3:09, 12 s):** NONE, screen only. the viewer must read what is on screen

[**Show:** The second query and its actual results. **Transition:** Place the two observed outcomes beside each other.]

We’ve checked two questions against a tiny collection.  
What happens when the meaning or vocabulary becomes more complicated?
> **Camera plan (3:21, 14 s):** FULL, head and shoulders, centred. explanation with nothing to read: the person carries it

## Explain the limit   3:35 to 4:20

Take the English word bat.  
It could mean an animal or something you use in baseball.
> **Camera plan (3:35, 10 s):** SMALL, window 18% width, corner (bottom-right). something is on screen but not dense: presence, small

Sharing a concept is only part of the task.  
The surrounding words help the encoder represent which meaning is intended.
> **Camera plan (3:45, 13 s):** SMALL, window 18% width, corner (bottom-right). something is on screen but not dense: presence, small

[**Camera:** Centered medium shot for the opening two sentences, then face hidden during the article insert. **Show:** The article’s contrasting bat examples. **Transition:** Return to the presenter in the same top right position.]

[**B roll:** **Find:** [The article](https://qdrant.tech/articles/minicoil-en-es/), under **From Words to Concepts**, in the illustration beneath **One Slot per Concept**. **Capture:** The relevant parts showing the animal and baseball meanings of bat. **Use during:** “The surrounding words help the encoder represent which meaning is intended.”]

The released version also has a limited set of trained concepts.  
Words outside that set keep ordinary word matching.  
That does not supply a missing translation match.
> **Camera plan (3:58, 17 s):** SMALL, window 18% width, corner (bottom-right). something is on screen but not dense: presence, small

So your own vocabulary belongs in the test.
> **Camera plan (4:15, 5 s):** FULL, head and shoulders, centred. something is on screen but not dense: presence, small (away from full for over 40 s: come back)

[**Show:** Return to the demonstration’s query box. **Transition:** Introduce the viewer’s practice task.]

## Give them something to try   4:20 to 5:00

Start with a few short English passages you can judge yourself.
> **Camera plan (4:20, 6 s):** SMALL, window 18% width, corner (bottom-right). something is on screen but not dense: presence, small

Write one Spanish question with an obvious answer.  
Then try a question where the surrounding words change the meaning.  
Finally, try a term from your own subject.
> **Camera plan (4:26, 14 s):** SMALL, window 18% width, corner (bottom-right). something is on screen but not dense: presence, small

[**Camera:** Small face in the same top right position. **Show:** Three prompts labeled Familiar question, Context question and Subject term. **Transition:** Bring back the search results.]

For each question, record whether the right passage appeared and where it ranked.
> **Camera plan (4:39, 7 s):** SMALL, window 18% width, corner (bottom-right). something is on screen but not dense: presence, small

If something looks wrong, keep that example and inspect it.
> **Camera plan (4:46, 5 s):** SMALL, window 18% width, corner (bottom-right). something is on screen but not dense: presence, small

That’s your first experiment.  
A few passages, three questions, and results you can check for yourself.
> **Camera plan (4:51, 9 s):** SMALL, window 18% width, corner (bottom-right). something is on screen but not dense: presence, small

[**Camera:** Return to a centered medium shot for the final two sentences. **Show:** The presenter closing the explanation. **Transition:** Finish on the invitation to try the small experiment.]

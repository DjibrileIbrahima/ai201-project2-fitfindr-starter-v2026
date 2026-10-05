# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
Two things on this path are outside a plain `if`. My query parser is a regex,
so a phrasing it doesn't expect ("under 30 bucks", "sz M") can produce wrong
filters and an empty search on a query that should match. And two of the three
tools call the model, so a rate limit or timeout can end a run early. One miss
in five allows for that; two would mean the parser or the error handling is
broken.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
This path never reaches the model. `search_listings` is a plain Python filter
over a fixed file, so the same query returns the same `[]` every time, and the
branch is a single check on that list. Nothing on the path is random, so any
miss is a bug in my code, not bad luck.

---

## 3. The searched item is the item every later tool receives

Given a query that matches, the listing passed to `suggest_outfit` has the same
`id` as `session["selected_item"]`, and that `id` equals
`session["search_results"][0]["id"]` — in 5 of 5 tries.

**Why this target:**
Moving the item from search to the next tool is plain assignment through the
session dict, with no model involved. If the ids ever differ, I've overwritten
or mixed up a session field, which is a bug, not variance. It also has to be
5 of 5 because a state mix-up wouldn't look like one: it would look like
`suggest_outfit` styling the wrong item, and I'd go blaming the prompt.

---

## 4. The fit card names the price and platform in two sentences

Given a query that matches, the fit card contains the selected item's price
written as `$NN`, contains its `platform` name, and is exactly two sentences —
in at least 4 of 5 tries.

**Why this target:**
These are the facts that make it a post about *this* find rather than a generic
caption, and price and platform are present on all 40 listings, so the card
never has an excuse to skip them. Not 5 of 5 because the model runs at
temperature 0.9 and can drop a detail or add a third sentence. "Exactly two
sentences" is the part I expect to slip. More than one miss would mean my
prompt isn't stating the rules clearly enough.

---

## 5. The size filter never returns the wrong size

For five size queries — `S`, `M`, `L`, `8` and `W30` — every listing that
`search_listings` returns has the requested size as a whole token of its `size`
field: `S/M` counts for `S`, `US 9` does not, and `US 8.5` does not count for
`8` — in 5 of 5 queries.

**Why this target:**
The data mixes four size systems (letters, `US` shoe sizes, `W`/`L` waists,
`One Size`), and a substring test fails on exactly these cases: `"s" in "us 9"`
is True and `"8" in "us 8.5"` is True. My filter compares whole tokens, which
is deterministic, so anything under 5 of 5 means the tokenizing is wrong. A
wrong size in the results reads to the user as a broken search, even though
every other part of the agent worked.


---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->

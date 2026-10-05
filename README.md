# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

FitFindr takes a plain-language thrift request like `'vintage graphic tee under $30, size M'` and searches 40 secondhand listings for the best match within that size and price. It then builds one outfit around the item using pieces from the user's own wardrobe, or general pieces if their wardrobe is empty. Finally it writes a two-sentence caption they could post about the find, naming the item, its price and the platform. If nothing matches, it stops before any of that and tells the user which part of the request to loosen.


---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters the 40 listings in `data/listings.json` by price ceiling and size, then ranks what's left by how many words from the description appear in each listing's title, description, category and style tags. It does not call the model.
- **Inputs:**
  - `description` (str): keywords for what the user wants, e.g. `"vintage graphic tee"`
  - `size` (str | None): size to filter by, matched case-insensitively against whole size tokens, not substrings. `"M"` matches `M`, `S/M` and `M/L` but not `W30 L30`. `"8"` matches `US 8` but not `US 8.5`. `One Size` listings never match a size request. `None` skips size filtering.
  - `max_price` (float | None): inclusive price ceiling. `30.0` keeps a $30.00 item. `None` skips price filtering.
- **Returns:** A `list[dict]` of at most `config.SEARCH_RESULT_LIMIT` (10) listing dicts, highest keyword score first. Each dict has `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand` (str or None) and `platform`.
- **When it has nothing:** Returns an empty list `[]`, never `None` and never an exception. This happens when no listing passes the price and size filters with a keyword score above zero. The loop branches on this.

### `suggest_outfit`

- **What it does:** Sends the thrifted item and the user's wardrobe to the model (through `generate()`) and asks for one outfit built around the item.
- **Inputs:**
  - `new_item` (dict): one listing dict, the item selected from the search results
  - `wardrobe` (dict): a dict with an `items` key holding a list of wardrobe item dicts (`id`, `name`, `category`, `colors`, `style_tags`, `notes`). The list may be empty.
- **Returns:** A non-empty `str` holding **one** outfit as a numbered list, one piece per line. The new item is one line, and every other line names a piece from the wardrobe exactly as its `name` field is written (e.g. "Chunky white sneakers").
- **When it has nothing:** If `wardrobe["items"]` is empty, it still returns a non-empty `str`: one outfit as a numbered list of general piece types (e.g. "white sneakers"), with no claim that the user owns them. It never returns `""` or `None`. If the model can't be reached, it doesn't catch the error. `ModelUnavailable` propagates to the loop.

### `create_fit_card`

- **What it does:** Sends the item and the outfit to the model (through `generate()`) and asks for a short caption someone would actually post about the find.
- **Inputs:**
  - `outfit` (str): the outfit string returned by `suggest_outfit`
  - `new_item` (dict): the same listing dict passed to `suggest_outfit`
- **Returns:** A `str` caption of exactly two short sentences, written like a social post rather than a product description. It mentions the item's `title`, `price` (as `$NN`) and `platform` once each, and mentions the `brand` only when it isn't `None`.
- **When it has nothing:** If `outfit` is empty or whitespace-only, it returns the exact string `"Couldn't write a fit card: no outfit suggestion was provided."` without calling the model and without raising. If the model can't be reached, `ModelUnavailable` propagates to the loop.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` naming the search and what to loosen (drop the size, raise the price limit, or use broader words), and return the session without calling `suggest_outfit` or `create_fit_card`. Otherwise take the first (highest-scoring) result as `session["selected_item"]` and go to `suggest_outfit`, then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex, in `agent.py::parse_query`. One pattern finds the price (`$30`, `under $30`, `under 30`), another finds the size (`size M`, `size S/M`, `size 8`, `size US 8.5`, `size W30 L30`). Both are cut out of the query, filler words like "looking for a" are removed, and what's left is the description. A phrasing the patterns don't cover, like "30 bucks", is left in the description and not used as a filter.

**What moves through the session:** In order: `query` → `parsed` (`description`, `size`, `max_price`) → `search_results` → `selected_item` (= `search_results[0]`) → `outfit_suggestion` → `fit_card`. Each tool reads its input from the session, not from a local variable: `suggest_outfit` gets `session["selected_item"]` and `session["wardrobe"]`, and `create_fit_card` gets `session["outfit_suggestion"]` and `session["selected_item"]`. `error` stays `None` unless the branch stops the run, and then the later fields stay `None`.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   1. Y2K Baby Tee — Butterfly Print
2. Baggy straight-leg jeans, dark wash
3. Black cropped zip hoodie
4. Chunky white sneakers
5. Black crossbody bag

  Fit card: Scored this butterfly baby tee for just $18 on depop, and it totally nails that ultimate Y2K mall-goth look. Pairing it with baggy denim and my favorite hoodie makes the whole outfit come together effortlessly.

0 model calls this session, 2 served from cache
```

**The empty-search branch**

```
$ python app.py ask 'designer ballgown size XXS under $5'

  Nothing matched 'designer ballgown' in size XXS under $5. You could drop the size, or raise the price limit, or try broader words, like 'jacket' instead of a specific style.

0 model calls this session
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"

```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
1. Vintage Levi's 501 Jeans — Medium Wash
2. White ribbed tank top
3. Vintage black denim jacket
4. Chunky white sneakers
5. Black crossbody bag
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Scored these vintage Levi's 501 jeans on Depop for just $38 and they give off the ultimate effortless streetwear vibe with my white sneakers.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1: the size filter in `search_listings`**

- *What I asked for:* I gave Claude my size rules for the spec: `S/M` should match a search for `S` or `M`, a search for `8` should not match `8.5`, and the price ceiling is inclusive. Then I asked it to build `search_listings` from that spec.
- *What came back:* A filter that splits sizes into whole-word tokens with a regex (`"S/M"` → `{s, m}`, `"US 8.5"` → `{us, 8.5}`) instead of a substring test, so `"s"` no longer matches `"US 9"`. It also proposed that `One Size` never matches a size request. When we tested it, the size filter was correct for `S`, `M`, `L`, `8` and `W30`, but a search for `'graphic tee'` also returned low-rise cargo pants, because their description says "great for layering with a long tee".
- *What I changed:* I didn't understand why `re` was imported, so I asked. I learned that the regex keeps `8.5` as one token, and that's what makes my "8 is not 8.5" rule work. Without it, `"US 8.5"` would split into `8` and `5` and match a size-8 search. I kept the cargo-pants result instead of patching it: it ranks below the real tees, and it shows a real limit of keyword scoring (it can't tell "is a tee" from "goes with a tee"). I'll come back to that in unit 4.

**Moment 2: parsing the query in `run_agent`**

- *What I asked for:* For Milestone 5, I asked Claude to wire the loop, which meant turning a sentence like `'vintage graphic tee under $30, size S/M'` into a description, a size and a max price before calling `search_listings`.
- *What came back:* `parse_query` in `agent.py`, which uses regex rather than asking the model. One pattern finds the price (`$30`, `under $30`, `under 30`), one finds the size (`size M`, `size S/M`, `size 8`, `size US 8.5`, `size W30 L30`), and whatever is left after cutting those and filler like "looking for a" becomes the description. Tested on the six example queries plus three harder ones, it parsed all nine correctly, including `'boots size US 8.5'` → size `US 8.5`.
- *What I changed:* I kept regex instead of a model call: it costs no requests, gives the same answer every time, and I can test it on its own. I also wrote down its limits rather than hiding them. It can't read "30 bucks" or "sz M". Those words stay in the description and aren't used as filters, so the search runs without the ceiling and nothing warns the user. That's exactly the "some phrasings will miss" risk in my criterion 1 reason, and it's why that target is 4 of 5, not 5 of 5. One behavior I noticed and decided to keep: asking for `S/M` only matches listings sized `S/M`, because my size rule needs every requested token to match.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**

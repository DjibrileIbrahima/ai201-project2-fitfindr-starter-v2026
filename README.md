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
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The searched item is the item every later tool receives | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card names the price and platform in two sentences | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. The size filter never returns the wrong size | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Full log: [results/run_2026-10-13_1824_before.md](results/run_2026-10-13_1824_before.md). Cache off, temperature 0.9, 50 model calls.

**Real output from one try**, pasted as text, naming the file and function
that produced it:

Criterion 4, all five tries. Produced by `run_eval.py::main` running `agent.py::run_agent`; each caption is written by `tools.py::create_fit_card`. Query `denim jacket under $50`, selected item `lst_007` Denim Jacket — Light Wash, Cropped ($42.0, poshmark).

```
Try 1: Scored this vintage Wrangler denim jacket on Poshmark for just $42 and it gives the ultimate 90s streetwear vibe. Paired it with khakis and chunky sneakers for the easiest casual fit.
Try 2: Scored this vintage Wrangler denim jacket on Poshmark for just $42 and it completely nails that effortless 90s streetwear vibe. The cropped light wash looks so good with wide-leg trousers for off-duty days.
Try 3: Scored this vintage Wrangler denim jacket on Poshmark for just $42 and it completely nails that effortless 90s streetwear vibe. The cropped light wash looks so good paired with wide-leg trousers and chunky sneakers for casual everyday wear.
Try 4: Score this vintage Wrangler denim jacket on Poshmark for only $42 and honestly the light wash cropped streetwear vibe is perfection. It looks so good paired with my go-to wide-leg khakis and chunky sneakers for an effortless off-duty fit.
Try 5: Scored this vintage Wrangler denim jacket on Poshmark for just $42 and it completely nails that effortless 90s streetwear vibe. The cropped light wash looks so good with wide-leg trousers and sneakers for running around the city.
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
| 1 | A matching query completes all three tools | 4 of 5 | MET (5/5) | All five tries show `stopped early: no` and a fit card in the session. |
| 2 | An impossible query stops before the second tool | 5 of 5 | MET (5/5) | All five show `search_results: (none)`, a message naming the size and the wording to change, and a trace that ends at step [2] with no `suggest_outfit` step. |
| 3 | The searched item is the item every later tool receives | 5 of 5 | MET (5/5) | In all five, `search_results[0]`, `selected_item` and the trace inputs to `suggest_outfit` [3] and `create_fit_card` [4] are all `lst_004`. |
| 4 | The fit card names the price and platform in two sentences | 4 of 5 | MET (5/5) | I read each card: all five contain `$42` and "Poshmark", and each has exactly two sentences (two full stops, no other sentence breaks). |
| 5 | The size filter never returns the wrong size | 5 of 5 | MET (5/5) | I checked every size in `search_results` for each of the five queries (S, M, L, 8, W30). Each contains the requested size as a whole token, and none is a `US` shoe size, a `One Size` or an `XL` for `L`. |

**Diagnoses**

No criterion missed, so there is no miss to diagnose. The run did show three things my criteria don't measure:

1. **Criterion 4 passed here but failed in unit 3, and the input explains it.** In my unit 3 terminal tests, 2 of 4 captions came out as one long sentence joined with "and". Those tests passed `create_fit_card` short hand-written outfits (`'jeans and white sneakers'`, or a three-line placeholder list). In the loop, it gets the full numbered outfit from `suggest_outfit`, which gives the model something to fill a second sentence with. The tool and prompt are the same; the input was richer. My criterion only tested the real-loop path, so it can't see the short-input failure.
2. **The caption ignores the item's title.** My Tool Inventory says `create_fit_card` mentions the item's `title`, but all five cards say "vintage Wrangler denim jacket" instead of "Denim Jacket — Light Wash, Cropped". It names the brand (which the prompt adds when there is one) and paraphrases the rest. That's a gap between the spec and the model's output, and criterion 4 doesn't check for the title, so it passed anyway.
3. **"Score this" instead of "Scored this"** appears in 2 of the 10 captions in this run (criterion 1 try 1, criterion 4 try 4). It reads as an instruction rather than a post. It's a model-output problem, not a tool or state problem.



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
$ python app.py ask 'vintage graphic tee under $30' --trace
[1] parse_query
      in:  vintage graphic tee under $30
      out: description='vintage graphic tee', size=None, max_price=30.0
[2] search_listings (via MCP)
      in:  description='vintage graphic tee', size=None, max_price=30.0
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    branch: results found, taking the first
[3] suggest_outfit
      in:  lst_002 Y2K Baby Tee — Butterfly Print, wardrobe: 10 items
      out: 1. Y2K Baby Tee — Butterfly Print 2. Baggy straight-leg jeans, dark wash 3. Black cropped zip hoodie 4. Chunky…
[4] create_fit_card
      in:  lst_002 Y2K Baby Tee — Butterfly Print, outfit: 148 chars
      out: Scored this butterfly baby tee for just $18 on depop, and it totally nails that ultimate Y2K mall-goth look. P…
```

**Empty search**

```
$ python app.py ask 'leather cowboy boots size US 12' --trace
[1] parse_query
      in:  leather cowboy boots size US 12
      out: description='leather cowboy boots', size='US 12', max_price=None
[2] search_listings (via MCP)
      in:  description='leather cowboy boots', size='US 12', max_price=None
      out: [] (empty)
      →    branch: empty, stopping before suggest_outfit

  Nothing matched 'leather cowboy boots' in size US 12. You could drop the size, or try broader words, like 'jacket' instead of a specific style.

0 model calls this session
```

**Model unreachable** (a fake `GEMINI_API_KEY` set for one command, cache off)

```
$ python app.py ask '90s track jacket in size M' --trace
[1] parse_query
      in:  90s track jacket in size M
      out: description='90s track jacket', size='M', max_price=None
[2] search_listings (via MCP)
      in:  description='90s track jacket', size='M', max_price=None
      out: 4 items: 90s Track Jacket — Navy/White Stripe, 90s Leather Bomber — Black, 90s Silk Slip Dress — Floral, Midi Length … +1 more
      →    branch: results found, taking the first
[3] suggest_outfit
      out: ModelUnavailable
      →    model unreachable: stopping with a message

  Found 90s Track Jacket — Navy/White Stripe ($45 on poshmark), but couldn't reach the model to run suggest_outfit, so there's no outfit or fit card this time. The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.
```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->
I registered `search_listings` in `mcp_server.py`, with a two-sentence description written for an agent that can't see my code: the price unit (USD, inclusive), the 10-result cap, and `[]` when nothing matches. My first draft was three paragraphs. It listed every field in a result and spelled out the size-matching rule with examples. I cut it down, because the type hints already publish the inputs, and the starter asks for one or two sentences. In `agent.py::run_agent`, the direct `search_listings(...)` call became `call_tool("search_listings", {...})`. Nothing else in the loop changed. `python mcp_client.py` lists the tool with `description: string` required and `size: string`, `max_price: number` optional, which matches my Tool Inventory. I compared the direct call against the MCP call on five queries (graphic tee ≤ $30, leather cowboy boots size US 12, track jacket size M, sneakers size 8, jeans W30). All five returned identical lists, including the empty one. That was the case I was watching, because the client turns empty text into `None`. It came back as `[]`, a real list, so the branch and criterion 2 behave exactly as before. The only visible difference is speed. Each call starts a new server process, so a search went from about 2 ms direct to 1.6–2.7 s over MCP (three timed calls). That's fine next to the model calls, but it's the cost of the seam.



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** One prompt, in `tools.py::create_fit_card`. The old prompt asked for "exactly two short sentences" but didn't say what either sentence was for. The new one gives each sentence a job: *"Sentence 1 is the find: the item's name, the price written exactly as $38, and the platform. Sentence 2 is how I'm wearing it and the vibe, using the outfit. End each sentence with a full stop. Don't join them into one."* Nothing else in the tool or the loop changed.

**Which failure it was meant to fix:** Diagnosis 1, the one-sentence caption. It never showed inside the loop, because the loop always passes a full numbered outfit. So I added a diagnostic scenario that calls `create_fit_card` directly with the short outfit from my unit 3 Sample Run (`'jeans and white sneakers'` on `lst_001`, the Levi's 501s at $38 on depop). I measured it **before** changing the prompt and committed that log first ([results/run_2026-10-14_0246_before-short.md](results/run_2026-10-14_0246_before-short.md)). It scored 3 of 5 against criterion 4's test ($NN, platform, two sentences). Tries 1 and 5 were one long sentence joined with "and", the same shape as in unit 3. The place is the model's output; the mechanism is that a short outfit left the second sentence with nothing of its own to say, and "two sentences" wasn't specific enough to stop the model merging them.

### Run Log — After

Full log: [results/run_2026-10-14_1800_after.md](results/run_2026-10-14_1800_after.md). Cache off, temperature 0.9, 55 model calls.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The searched item is the item every later tool receives | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card names the price and platform in two sentences | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. The size filter never returns the wrong size | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| Fit card from a short outfit _(diagnostic, criterion 4's test)_ | 4 of 5 | PASS | PASS | PASS | PASS | PASS | 5/5 (before: 3/5) |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->

Yes, on the failure it targeted. The short-outfit caption went from 3 of 5 to 5 of 5 under the same scenario, measured the same way, before and after one prompt change. For example: *"Just scored these vintage Levi's 501 jeans for $38 on Depop. I'm keeping it simple with white sneakers for the ultimate casual street vibe."* Criteria 1–5 all stayed at 5/5, so nothing regressed.

It also made the captions worse in a way none of my criteria measure. Almost all 30 cards in the after run follow one template: *"Scored this [item] for $N on [platform]. I'm wearing it with [list of the outfit pieces] for the ultimate … vibe."* Telling sentence 2 to use the outfit made the model list the outfit, so the second sentence reads like an inventory rather than a post. Before, the captions varied more and talked about the vibe. I fixed the count by fixing the structure, and the structure is now visible in every card. One side effect went the right way: because sentence 1 now asks for "the item's name", some cards use the exact title ("Y2K Baby Tee — Butterfly Print", "Platform Sneakers — White Chunky Sole"), where before none did.



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->

No criterion is missed, before or after. These are the problems the run showed that my criteria don't catch:

1. **The captions are formulaic now.** The template above is the cost of my fix. Next I'd tell sentence 2 to pick *one* piece of the outfit and describe the feel, not list every piece. Then I'd add a criterion I can count, like "no two of five cards share the same second-sentence opening." I stopped here because Milestone 5 asks for one change measured properly, and a second prompt change would have mixed two effects in one after-run.
2. **"Score this" instead of "Scored this"** appeared in 3 of 30 cards before (25 in the before run plus 5 in the short-outfit before run) and 4 of 30 after. My change didn't target it, and it didn't fix it. One line in the prompt ("write it in the past tense, as something I already bought") is the obvious next try, measured by counting "Score this" across a run.
3. **The title still isn't used reliably.** My Tool Inventory says the card mentions the item's title. After the change some cards do and most still paraphrase it ("vintage Wrangler denim jacket"). Criterion 4 never checked the title. To measure it, I'd add a revision under criterion 4 (keeping the original line) that requires the exact `title`.
4. **The keyword search can't tell "is a tee" from "goes with a tee".** `'graphic tee'` still returns low-rise cargo pants because their description says "layering with a long tee". It ranks below the real tees, so it never became the selected item in any run. Weighting the title and category above the description would fix it.
5. **The query parser misses some phrasings.** "30 bucks" and "sz M" aren't recognised, so the search runs without that filter and nothing warns the user. My criterion 1 target (4 of 5) allows for this, but none of my scenarios uses those phrasings, so it was never tested.



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

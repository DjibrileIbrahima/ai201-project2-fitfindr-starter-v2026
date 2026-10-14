"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Three scenarios are filled in to show the shape. Add or change whatever your
own criteria need — these are a starting point, not a fixed set.
"""

SCENARIOS = [
    {
        # A query the data can match. Criterion 1.
        "name": "matching query completes",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        # A query nothing can match. Criterion 2 — the branch.
        "name": "impossible query stops early",
        "query": "leather cowboy boots size US 12",
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        # Criterion 3 — state. PASS when the trace's suggest_outfit and
        # create_fit_card inputs show the same id as selected_item, and that
        # id is the first one in search_results.
        "name": "searched item reaches every later tool",
        "query": "90s track jacket in size M",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        # Criterion 4 — the fit card. The same query five times, so the only
        # thing varying is the model. PASS when the card has the price as $NN,
        # the platform, and exactly two sentences.
        "name": "fit card names price and platform in two sentences",
        "query": "denim jacket under $50",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        # Criterion 5 — sizes. Five different sizes, one per try. "vintage"
        # matches almost every listing, so the size filter does all the
        # work. The US 8 shoe isn't tagged vintage, hence "sneakers" there.
        # PASS when every size in search_results contains the requested size
        # as a whole token.
        "name": "size filter returns only the requested size",
        "query": "vintage size S",
        "queries": [
            "vintage size S",
            "vintage size M",
            "vintage size L",
            "sneakers size 8",
            "vintage size W30",
        ],
        "wardrobe": "example",
        "criterion": 5,
    },
    {
        # Diagnostic for the improvement (Milestone 5). create_fit_card called
        # directly with a short outfit — the README Sample Run input that gave
        # a one-sentence card in unit 3. The loop always passes a full outfit,
        # so criterion 4 can't see this case. PASS when the card has $38,
        # "depop" and exactly two sentences, the same test as criterion 4.
        "name": "fit card from a short outfit",
        "tool": "create_fit_card",
        "outfit": "jeans and white sneakers",
        "item_id": "lst_001",
        "query": "create_fit_card('jeans and white sneakers', lst_001) — direct, no loop",
        "wardrobe": "example",
        "criterion": None,
    },
    {
        # A user with nothing saved. One of unit 4's three failure modes.
        "name": "empty wardrobe",
        "query": "denim jacket under $50",
        "wardrobe": "empty",
        "criterion": None,
    },
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems

"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    listings = load_listings()

    if max_price is not None:
        listings = [l for l in listings if l["price"] <= max_price]

    if size:
        wanted = _tokens(size)
        listings = [l for l in listings if _size_matches(wanted, l["size"])]

    query_words = _tokens(description) - _STOPWORDS
    if not query_words:
        return []

    scored = []
    for listing in listings:
        text = " ".join([
            listing["title"],
            listing["description"],
            listing["category"],
            " ".join(listing["style_tags"]),
        ])
        score = len(query_words & _tokens(text))
        if score > 0:
            scored.append((score, listing))

    # sorted() is stable, so equal scores keep the order they have in the file
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [listing for _, listing in scored[:config.SEARCH_RESULT_LIMIT]]


# Words that say nothing about the item, so they shouldn't earn a listing a point.
_STOPWORDS = {"a", "an", "the", "and", "or", "for", "in", "with", "of", "some",
              "looking", "want", "need", "size", "under", "below", "less", "than"}


def _tokens(text: str) -> set[str]:
    """Lowercase whole words. 'S/M' -> {'s', 'm'}, 'US 8.5' -> {'us', '8.5'}."""
    return set(re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", text.lower()))


def _size_matches(wanted: set[str], listing_size: str) -> bool:
    """
    Every token of the requested size has to be a whole token of the listing's
    size. Whole tokens, not substrings: 'S' matches 'S/M' but not 'US 9', and
    '8' matches 'US 8' but not 'US 8.5'. 'One Size' never matches a request.
    """
    if listing_size.lower().startswith("one size"):
        return False
    return wanted <= _tokens(listing_size)


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    items = wardrobe.get("items") or []

    if items:
        owned = "\n".join(
            f"- {w['name']} ({w['category']}; {', '.join(w['colors'])})" for w in items
        )
        prompt = (
            f"I just thrifted this item:\n{_describe_item(new_item)}\n\n"
            f"These are the clothes I already own:\n{owned}\n\n"
            "Build ONE outfit around the thrifted item. Write it as a numbered "
            "list, one piece per line. Line 1 is the thrifted item. Every other "
            "line must be a piece from my list, copied exactly as it is written "
            "before the brackets. Don't add anything I don't own. Don't write "
            "anything before or after the list."
        )
    else:
        prompt = (
            f"I just thrifted this item:\n{_describe_item(new_item)}\n\n"
            "I haven't told you what else I own. Build ONE outfit around the "
            "thrifted item. Write it as a numbered list, one piece per line. "
            "Line 1 is the thrifted item. Every other line is a general kind of "
            "piece (like 'white sneakers'), not a specific product, and don't "
            "say or imply that I own it. Don't write anything before or after "
            "the list."
        )

    response = generate(prompt).strip()
    if not response:
        # The spec promises a non-empty string, even if the model sends nothing.
        return f"1. {new_item['title']}"
    return response


def _describe_item(item: dict) -> str:
    """The listing in a few lines. Brand only when there is one — most have none."""
    lines = [
        f"{item['title']} ({item['category']})",
        f"Colors: {', '.join(item['colors'])}",
        f"Style: {', '.join(item['style_tags'])}",
    ]
    if item.get("brand"):
        lines.append(f"Brand: {item['brand']}")
    return "\n".join(lines)


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    if not outfit or not outfit.strip():
        return "Couldn't write a fit card: no outfit suggestion was provided."

    brand_rule = (
        f"Mention the brand, {new_item['brand']}, once. "
        if new_item.get("brand") else
        "There is no brand, so don't mention one. "
    )
    prompt = (
        f"I just thrifted this:\n{_describe_item(new_item)}\n"
        f"Price: {_price(new_item['price'])}\n"
        f"Platform: {new_item['platform']}\n\n"
        f"I'm wearing it like this:\n{outfit}\n\n"
        "Write the caption I'd post about this find. Exactly two short "
        "sentences, casual, like a real post rather than a product description, "
        "and specific about the vibe. Mention the item's name, the price written "
        f"exactly as {_price(new_item['price'])}, and the platform once each. "
        f"{brand_rule}"
        "Write only the caption."
    )
    return generate(prompt).strip()


def _price(price: float) -> str:
    """38.0 -> '$38', 12.5 -> '$12.50'."""
    return f"${price:.0f}" if price == int(price) else f"${price:.2f}"

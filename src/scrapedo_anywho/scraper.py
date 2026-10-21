"""High-level helpers: profile, name search and reverse phone lookup."""

import re

from .client import BASE_URL, NotFoundError, fetch
from .parsers import parse_phone, parse_profile, parse_search

AGE_RANGES = {"0-30", "31-60", "61-80", "80"}


def build_search_url(first_name, last_name, state=None, city=None, age_range=None):
    """Build a name search URL. State is the full name ("new york"), not "NY"."""
    path = f"/people/{first_name}+{last_name}"
    if state:
        path += f"/{state}"
        if city:
            path += f"/{city}"
    url = BASE_URL + path.lower().replace(" ", "+")
    if age_range:
        if age_range not in AGE_RANGES:
            raise ValueError(f"age_range must be one of {sorted(AGE_RANGES)}")
        url += f"?age_range={age_range}"
    return url


def get_profile(profile_url, token=None, **kwargs):
    """Scrape one profile page: name, exact age, aliases, address, phones, emails, history, relatives."""
    return parse_profile(fetch(profile_url, token=token, **kwargs))


def search(first_name, last_name, state=None, city=None, age_range=None, max_pages=4, token=None, **kwargs):
    """Scrape a name search, following "Next Page" links.

    AnyWho never serves more than 20 results (4 pages of 5) per query, so the default
    of 4 pages covers a full search. To reach more people, split the query by state,
    city or age range. Returns an empty list when the search has no matches.
    """
    next_url = build_search_url(first_name, last_name, state, city, age_range)
    rows = []
    page = 1
    while next_url and page <= max_pages:
        try:
            html = fetch(next_url, token=token, **kwargs)
        except NotFoundError:
            break
        page_rows, next_url = parse_search(html)
        rows.extend(page_rows)
        page += 1
    return rows


def reverse_phone(phone_number, token=None, **kwargs):
    """Reverse phone lookup: phone type, carrier, locations, spam check and owner records."""
    digits = re.sub(r"\D", "", str(phone_number))
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10 or digits[0] in "01":
        raise ValueError("Expected a 10-digit US number whose area code does not start with 0 or 1")
    return parse_phone(fetch(f"{BASE_URL}/phone/{digits}", token=token, **kwargs))

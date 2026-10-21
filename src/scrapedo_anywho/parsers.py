"""HTML parsers for AnyWho profile, name search and reverse phone pages.

AnyWho has no Person JSON-LD and no __NEXT_DATA__ blob, and its Tailwind classes
change with any restyle. These parsers rely on what a restyle is unlikely to touch:
section ids (#phones, #addresses, #records), the show-more-item card class,
aria-labels and label text like "Lives in:".
"""

import re

from bs4 import BeautifulSoup

BASE_URL = "https://www.anywho.com"


def clean(element, strip_chars=None):
    """Collapse whitespace; return "" for a missing element."""
    if element is None:
        return ""
    text = " ".join(element.get_text().split())
    return text.strip(strip_chars) if strip_chars else text


def make_soup(html):
    """Parse HTML and restore the values AnyWho blurs with CSS.

    AnyWho sends the hidden characters (last phone digits, house numbers, email
    usernames, owner names) in each span's data-content attribute and paints them
    with a blurred ::before pseudo-element. Writing the attribute into the span as
    text makes every later get_text() call read the full value.
    """
    soup = BeautifulSoup(html, "html.parser")
    for span in soup.select("span[data-content]"):
        span.string = span["data-content"]
    return soup


def _values_after(label):
    """Collect the <div> values that follow a label, up to the next label."""
    values = []
    for sibling in label.find_next_siblings():
        if sibling.name == "h3":
            break
        if sibling.name == "div":
            values.append(clean(sibling, " •"))
    return values


def parse_profile(html):
    """Parse an AnyWho profile page (/people/{first}+{last}/{state}/{city}/{id})."""
    soup = make_soup(html)

    # h1 reads "Full Name, Age"
    header = soup.find("h1")
    name, _, age = clean(header).partition(", ")
    aliases = clean(header.find_next_sibling("p")).replace("Aka:", "").strip() if header else ""

    # Summary links the current address as "street, city, state, zip".
    # rsplit from the right keeps a comma inside the street ("Rd, Apt 4") intact.
    current = clean(soup.select_one('#summary a[href="#addresses"]'))
    parts = [part.strip() for part in current.rsplit(",", 3)]
    if len(parts) == 4:
        street, city, state, zipcode = parts
    else:
        street, city, state, zipcode = current, "", "", ""

    phones = []
    for card in soup.select("#phones .show-more-item"):
        spans = card.find_all("span")
        phones.append({"number": clean(card.find("div")), "carrier": clean(spans[-1]) if spans else ""})

    emails = [clean(card.find("div")) for card in soup.select("#emails .show-more-item")]
    relatives = [clean(h3).replace("Relative data result:", "").strip() for h3 in soup.select("#family h3")]

    # First address card is the current one, the rest is history.
    # Each card's <p> reads "City, ST • YYYY-YYYY": years lived, not a ZIP+4.
    past_addresses = []
    for card in soup.select("#addresses .show-more-item")[1:]:
        city_state, _, years = clean(card.find("p")).partition("•")
        past_addresses.append(
            {"street": clean(card.find("h4")), "city_state": city_state.strip(), "years": years.strip()}
        )

    return {
        "name": name,
        "age": age,
        "aliases": aliases,
        "address": {"street": street, "city": city, "state": state, "zip": zipcode},
        "phones": phones,
        "emails": emails,
        "past_addresses": past_addresses,
        "relatives": relatives,
    }


def parse_search(html):
    """Parse one AnyWho name search page. Returns (rows, next_url)."""
    soup = make_soup(html)
    rows = []
    for card in soup.select("#name-search-results > div"):
        heading = card.find("h2")
        if heading is None:
            continue
        # Card header reads "Full Name, Age 42"
        name, _, age = clean(heading.parent).partition(", Age")

        # Each row is an <h3> label ("Lives in:", "Emails:"...) followed by one <div> per value
        fields = {}
        for h3 in card.find_all("h3"):
            fields[clean(h3).rstrip(":")] = _values_after(h3)

        link = card.select_one('a[variation="invisible-wrapper"]')
        rows.append(
            {
                "name": name.strip(),
                "age": age.strip(),
                "aliases": fields.get("AKA", []),
                "address": " | ".join(fields.get("Lives in", [])),
                "past_addresses": fields.get("Used to live in", []),
                "phones": fields.get("Phone number(s)", []),
                "emails": fields.get("Emails", []),
                "relatives": fields.get("May be related to", []),
                "profile_url": BASE_URL + link["href"] if link and link.get("href") else "",
            }
        )

    next_link = soup.select_one('nav[aria-label="Pagination"] a[aria-label="Next Page"]')
    next_url = BASE_URL + next_link["href"] if next_link and next_link.get("href") else None
    return rows, next_url


def _field(scope, label):
    """Labels like "PHONE TYPE:" are plain text; the value is the label element's next sibling."""
    element = scope.find(string=label)
    if element is None:
        return ""
    return re.sub(r"\s*•\s*", " | ", clean(element.parent.find_next_sibling())).strip(" |")


def parse_phone(html):
    """Parse an AnyWho reverse phone lookup page (/phone/{10 digits})."""
    soup = make_soup(html)

    # "+2 more" links only jump to the owner cards below, so drop them from the summary
    for link in soup.select('a[href="#records"]'):
        link.decompose()

    owners = []
    for owner in soup.select("#records .show-more-item"):
        owners.append(
            {
                "name": clean(owner.find("h4")),
                "age": _field(owner, "AGE:"),
                "address": _field(owner, "ADDRESS:"),
                "relatives": _field(owner, "RELATIVES:"),
            }
        )

    return {
        "phone": clean(soup.find("h1")).replace("Who Owns", "").strip(" ?"),
        "locations": _field(soup, "LOCATIONS:"),
        "phone_type": _field(soup, "PHONE TYPE:"),
        "carrier": _field(soup, "PHONE CARRIER:"),
        "spam_check": _field(soup, "SPAM CHECK:"),
        "owners": owners,
    }

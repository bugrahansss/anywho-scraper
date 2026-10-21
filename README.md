# AnyWho Scraper (Python)

Scrape [AnyWho](https://www.anywho.com) people search pages with Python: **profiles**, **name search to CSV** and **reverse phone lookup**. Built on the [Scrape.do](https://scrape.do) web scraping API.

- Returns the full values AnyWho blurs on screen: last phone digits, house and unit numbers, email usernames, owner names
- 1 Scrape.do credit per page, no headless browser, no `render=true`
- Works as a command line tool or a Python library

> Full walkthrough with every selector explained: [AnyWho.com Scraping: Extract People Search and Reverse Lookup Data](https://scrape.do/blog/anywho-scraping/)

## Install

```bash
pip install scrapedo-anywho
```

Get a free token at [dashboard.scrape.do/signup](https://dashboard.scrape.do/signup) (1,000 free credits a month = 1,000 AnyWho pages), then:

```bash
export SCRAPEDO_TOKEN="your_token"
```

## Command line

```bash
# Profile page
anywho profile "https://www.anywho.com/people/john+smith/texas/austin/a123456789"

# Name search, nationwide or by state, saved to CSV
anywho search john smith --state "new york" --csv results.csv

# Reverse phone lookup
anywho phone 6025550138
```

## Python

```python
from scrapedo_anywho import get_profile, search, reverse_phone

profile = get_profile("https://www.anywho.com/people/john+smith/texas/austin/a123456789")
rows = search("john", "smith", state="new york")        # up to 20 results
phone = reverse_phone("(602) 555-0138")                  # any 10-digit US format
```

## What you get

All sample values below are fictional.

**Profile**

```json
{
  "name": "Anakin S Skywalker",
  "age": "41",
  "aliases": "Darth Vader and Ani Skywalker",
  "address": {"street": "1138 Dune Sea Rd, Apt 4", "city": "Mos Espa", "state": "AZ", "zip": "85001"},
  "phones": [{"number": "(602) 555-0138", "carrier": "Verizon Wireless"}],
  "emails": ["anakin.skywalker@example.com"],
  "past_addresses": [{"street": "501 Temple Way, Apt 12", "city_state": "Galactic City, NY", "years": "2010-2019"}],
  "relatives": ["Padme Amidala", "Luke Skywalker", "Leia Organa"]
}
```

**Name search** returns one row per person with age, aliases, current and past addresses, phones, emails, relatives and `profile_url`. CSV columns:

`name, age, aliases, address, past_addresses, phones, emails, relatives, profile_url`

**Reverse phone** returns phone type, carrier, locations, spam check and owner records (name, age, street, relatives).

## How it works

1. **The block is a user agent check, not a bot wall.** AnyWho answers `python-requests` and `HeadlessChrome` with a CloudFront 403, whatever the country. A default Scrape.do request with `geoCode=us` gets a 200 for 1 credit. If 403s show up at volume, add `--super` (or `super_proxy=True`) for premium proxies at 10 credits.
2. **No JSON to parse.** AnyWho has no `Person` JSON-LD and no `__NEXT_DATA__`, so the parsers use selectors a restyle is unlikely to touch: section ids (`#phones`, `#addresses`, `#records`), the `show-more-item` card class, `aria-label`s and label text.
3. **The blur is CSS.** Hidden characters ship in each span's `data-content` attribute and are painted with a blurred `::before`. The parser writes every `data-content` value into its span before reading the page:

```python
for span in soup.select("span[data-content]"):
    span.string = span["data-content"]
```

## Limits

- A name search tops out at 20 results (4 pages of 5). Split by state, city or `--age-range` (`0-30`, `31-60`, `61-80`, `80`) to reach more people.
- A search with no matches is a real 404; `search()` returns an empty list.
- Emails on reverse phone owner cards stay behind AnyWho's paywall ("See available results") and are not returned.

## Responsible use

The data on AnyWho belongs to real people. AnyWho is not a consumer reporting agency: do not use this data for employment, tenant screening, credit or any other decision regulated by the [FCRA](https://www.ftc.gov/legal-library/browse/statutes/fair-credit-reporting-act). Honor opt-out requests, follow the privacy laws that apply to you (CCPA, GDPR and others) and check AnyWho's terms before you run anything at scale. This is not legal advice.

## Tests

```bash
pip install .
python -m unittest discover -s tests -v
```

Tests run offline against fictional fixture pages.

## More scrapers

Other people search sites in the same series: [TruePeopleSearch](https://scrape.do/blog/true-people-search-scraping/), [Whitepages](https://scrape.do/blog/white-pages-scraping/), [FastPeopleSearch](https://scrape.do/blog/fast-people-search-scraping/), [PeopleSearchNow](https://scrape.do/blog/people-search-now-scraping/).

---

Built by [Scrape.do](https://scrape.do), the web scraping API that handles proxies, retries and anti-bot so you can focus on parsing. MIT licensed.

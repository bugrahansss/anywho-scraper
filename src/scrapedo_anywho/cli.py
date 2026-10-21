"""Command line: anywho profile URL | anywho search FIRST LAST | anywho phone NUMBER"""

import argparse
import csv
import json
import sys

from .client import ScrapeDoError
from .scraper import get_profile, reverse_phone, search

CSV_COLUMNS = ["name", "age", "aliases", "address", "past_addresses", "phones", "emails", "relatives", "profile_url"]


def _write_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_COLUMNS)
        for row in rows:
            writer.writerow(
                [" | ".join(row[col]) if isinstance(row[col], list) else row[col] for col in CSV_COLUMNS]
            )


def main(argv=None):
    parser = argparse.ArgumentParser(prog="anywho", description="Scrape AnyWho with the Scrape.do API.")
    parser.add_argument("--token", help="Scrape.do token (defaults to the SCRAPEDO_TOKEN environment variable)")
    parser.add_argument("--super", dest="super_proxy", action="store_true", help="Use premium proxies (10 credits)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_profile = sub.add_parser("profile", help="Scrape a profile page")
    p_profile.add_argument("url", help="Profile URL, e.g. https://www.anywho.com/people/john+smith/texas/austin/a123456789")

    p_search = sub.add_parser("search", help="Search by name (up to 20 results)")
    p_search.add_argument("first_name")
    p_search.add_argument("last_name")
    p_search.add_argument("--state", help='Full state name, e.g. "new york"')
    p_search.add_argument("--city")
    p_search.add_argument("--age-range", choices=["0-30", "31-60", "61-80", "80"])
    p_search.add_argument("--csv", help="Write results to this CSV file instead of printing JSON")

    p_phone = sub.add_parser("phone", help="Reverse phone lookup")
    p_phone.add_argument("number", help="10-digit US number, e.g. 6025550138")

    args = parser.parse_args(argv)
    options = {"token": args.token, "super_proxy": args.super_proxy}

    try:
        if args.command == "profile":
            result = get_profile(args.url, **options)
        elif args.command == "search":
            result = search(args.first_name, args.last_name, args.state, args.city, args.age_range, **options)
            if args.csv:
                _write_csv(result, args.csv)
                print(f"Saved {len(result)} results to {args.csv}")
                return 0
        else:
            result = reverse_phone(args.number, **options)
    except (ScrapeDoError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

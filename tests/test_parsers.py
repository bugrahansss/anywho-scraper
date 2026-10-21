"""Offline tests against fictional fixture pages. Run with: python -m unittest discover -s tests"""

import pathlib
import unittest

from scrapedo_anywho import build_search_url, parse_phone, parse_profile, parse_search
from scrapedo_anywho.scraper import reverse_phone

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def load(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.data = parse_profile(load("profile.html"))

    def test_name_age_aliases(self):
        self.assertEqual(self.data["name"], "Anakin S Skywalker")
        self.assertEqual(self.data["age"], "41")
        self.assertEqual(self.data["aliases"], "Darth Vader and Ani Skywalker")

    def test_current_address_keeps_comma_inside_street(self):
        self.assertEqual(
            self.data["address"],
            {"street": "1138 Dune Sea Rd, Apt 4", "city": "Mos Espa", "state": "AZ", "zip": "85001"},
        )

    def test_blurred_values_are_unmasked(self):
        self.assertEqual(self.data["phones"][0], {"number": "(602) 555-0138", "carrier": "Verizon Wireless"})
        self.assertEqual(self.data["emails"], ["anakin.skywalker@example.com"])

    def test_history_and_relatives(self):
        self.assertEqual(len(self.data["past_addresses"]), 2)
        self.assertEqual(
            self.data["past_addresses"][0],
            {"street": "501 Temple Way, Apt 12", "city_state": "Galactic City, NY", "years": "2010-2019"},
        )
        self.assertEqual(self.data["relatives"], ["Padme Amidala", "Luke Skywalker", "Leia Organa"])


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.rows, self.next_url = parse_search(load("search.html"))

    def test_cards(self):
        self.assertEqual(len(self.rows), 2)
        first = self.rows[0]
        self.assertEqual(first["name"], "Anakin S Skywalker")
        self.assertEqual(first["age"], "41")
        self.assertEqual(first["aliases"], ["Darth Vader", "Ani Skywalker"])
        self.assertEqual(first["address"], "1138 Dune Sea Rd, Apt 4, Mos Espa, AZ")
        self.assertEqual(first["past_addresses"], ["501 Temple Way, Apt 12, Galactic City, NY"])
        self.assertEqual(first["phones"], ["(602) 555-0138", "(602) 555-0199"])
        self.assertEqual(first["emails"], ["anakin.skywalker@example.com"])
        self.assertEqual(
            first["profile_url"], "https://www.anywho.com/people/anakin+skywalker/arizona/mos+espa/a1000000001"
        )

    def test_missing_rows_are_empty_not_errors(self):
        second = self.rows[1]
        self.assertEqual(second["emails"], [])
        self.assertEqual(second["phones"], [])
        self.assertEqual(second["relatives"], ["Anakin S Skywalker"])

    def test_next_page(self):
        self.assertEqual(self.next_url, "https://www.anywho.com/people/anakin+skywalker?page=2")


class PhoneTests(unittest.TestCase):
    def setUp(self):
        self.data = parse_phone(load("phone.html"))

    def test_summary(self):
        self.assertEqual(self.data["phone"], "(602) 555-0138")
        self.assertEqual(self.data["locations"], "Mos Espa, AZ | Anchorhead, AZ")
        self.assertEqual(self.data["phone_type"], "Wireless")
        self.assertEqual(self.data["carrier"], "Verizon Wireless")
        self.assertEqual(self.data["spam_check"], "No spam reports have been found.")

    def test_owner_records(self):
        self.assertEqual(len(self.data["owners"]), 2)
        self.assertEqual(
            self.data["owners"][0],
            {
                "name": "Anakin S Skywalker",
                "age": "41",
                "address": "1138 Dune Sea Rd, Apt 4",
                "relatives": "Padme Amidala | Luke Skywalker",
            },
        )


class UrlTests(unittest.TestCase):
    def test_search_url(self):
        self.assertEqual(
            build_search_url("John", "Smith", "New York"), "https://www.anywho.com/people/john+smith/new+york"
        )
        self.assertEqual(
            build_search_url("john", "smith", age_range="31-60"),
            "https://www.anywho.com/people/john+smith?age_range=31-60",
        )

    def test_bad_age_range(self):
        with self.assertRaises(ValueError):
            build_search_url("john", "smith", age_range="20-40")

    def test_bad_phone_number_is_rejected_before_any_request(self):
        with self.assertRaises(ValueError):
            reverse_phone("0125550138", token="unused")


if __name__ == "__main__":
    unittest.main()

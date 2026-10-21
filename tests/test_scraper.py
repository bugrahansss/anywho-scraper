"""Pagination and error handling, with the network call mocked out."""

import pathlib
import unittest
from unittest import mock

from scrapedo_anywho import NotFoundError, search

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
SEARCH_HTML = (FIXTURES / "search.html").read_text(encoding="utf-8")
LAST_PAGE_HTML = SEARCH_HTML.replace('<a aria-label="Next Page" href="/people/anakin+skywalker?page=2">Next</a>', "")


class SearchPaginationTests(unittest.TestCase):
    @mock.patch("scrapedo_anywho.scraper.fetch")
    def test_follows_next_page_until_last(self, fetch):
        fetch.side_effect = [SEARCH_HTML, LAST_PAGE_HTML]
        rows = search("anakin", "skywalker", token="test")
        self.assertEqual(len(rows), 4)
        self.assertEqual(fetch.call_count, 2)
        self.assertEqual(fetch.call_args_list[1].args[0], "https://www.anywho.com/people/anakin+skywalker?page=2")

    @mock.patch("scrapedo_anywho.scraper.fetch")
    def test_stops_at_max_pages(self, fetch):
        fetch.return_value = SEARCH_HTML
        search("anakin", "skywalker", max_pages=4, token="test")
        self.assertEqual(fetch.call_count, 4)

    @mock.patch("scrapedo_anywho.scraper.fetch")
    def test_no_results_is_an_empty_list(self, fetch):
        fetch.side_effect = NotFoundError(404, "https://www.anywho.com/people/nobody+here")
        self.assertEqual(search("nobody", "here", token="test"), [])


if __name__ == "__main__":
    unittest.main()

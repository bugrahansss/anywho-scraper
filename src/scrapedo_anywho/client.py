"""Thin wrapper around the Scrape.do API for AnyWho pages."""

import os

import requests

API_URL = "https://api.scrape.do/"
BASE_URL = "https://www.anywho.com"


class ScrapeDoError(Exception):
    """Raised when Scrape.do returns anything other than a 200 or a 404."""

    def __init__(self, status_code, url):
        self.status_code = status_code
        self.url = url
        super().__init__(f"Request failed with status {status_code} for {url}")


class NotFoundError(ScrapeDoError):
    """AnyWho answers a search with no matches with a real 404."""


def get_token(token=None):
    token = token or os.environ.get("SCRAPEDO_TOKEN")
    if not token:
        raise ValueError(
            "No Scrape.do token. Pass token=... or set the SCRAPEDO_TOKEN environment variable. "
            "Get a free token at https://dashboard.scrape.do/signup"
        )
    return token


def fetch(url, token=None, geo_code="us", super_proxy=False, timeout=60):
    """Fetch an AnyWho page through Scrape.do and return its HTML.

    AnyWho blocks library and headless user agents (python-requests, HeadlessChrome)
    with a CloudFront 403. A default Scrape.do request with geoCode=us costs 1 credit
    and gets through. If 403s show up at volume, pass super_proxy=True (10 credits).
    """
    params = {"token": get_token(token), "url": url, "geoCode": geo_code}
    if super_proxy:
        params["super"] = "true"
    # Passing the target as a param lets requests handle the URL encoding
    response = requests.get(API_URL, params=params, timeout=timeout)
    if response.status_code == 404:
        raise NotFoundError(404, url)
    if response.status_code != 200:
        raise ScrapeDoError(response.status_code, url)
    return response.text

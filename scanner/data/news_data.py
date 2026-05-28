"""News and sentiment data from free public sources."""
from __future__ import annotations

import re
import html
from datetime import datetime, timezone
from typing import Any

import requests
from bs4 import BeautifulSoup


_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; EquitiesScanner/1.0)",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}
_TIMEOUT = 10


def _fetch_rss(url: str) -> list[dict]:
    """Parse an RSS feed and return a list of article dicts."""
    items = []
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "xml")
        for item in soup.find_all("item")[:15]:
            title = item.find("title")
            desc = item.find("description")
            link = item.find("link")
            pub = item.find("pubDate")
            items.append({
                "title": html.unescape(title.get_text(strip=True)) if title else "",
                "description": html.unescape(
                    BeautifulSoup(desc.get_text(strip=True), "html.parser").get_text()
                    if desc else ""
                )[:300],
                "link": link.get_text(strip=True) if link else "",
                "published": pub.get_text(strip=True) if pub else "",
            })
    except Exception:
        pass
    return items


def fetch_yahoo_news(ticker: str) -> list[dict]:
    """Yahoo Finance RSS news for a ticker."""
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
    return _fetch_rss(url)


def fetch_seeking_alpha_news(ticker: str) -> list[dict]:
    """Seeking Alpha RSS for a ticker (public feed)."""
    url = f"https://seekingalpha.com/api/sa/combined/{ticker}.xml"
    return _fetch_rss(url)


def fetch_reuters_news(ticker: str) -> list[dict]:
    """Reuters RSS search for company name / ticker."""
    url = f"https://feeds.reuters.com/reuters/businessNews"
    articles = _fetch_rss(url)
    ticker_upper = ticker.upper()
    return [a for a in articles if ticker_upper in a.get("title", "").upper()
            or ticker_upper in a.get("description", "").upper()]


def fetch_sec_filings(ticker: str) -> list[dict]:
    """Recent SEC EDGAR filings via the public EDGAR full-text search."""
    filings = []
    try:
        url = (
            f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22"
            f"&dateRange=custom&startdt={(datetime.now().year - 1)}-01-01"
            f"&forms=10-K,10-Q,8-K,4"
        )
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        data = resp.json()
        hits = data.get("hits", {}).get("hits", [])[:10]
        for h in hits:
            src = h.get("_source", {})
            filings.append({
                "form_type": src.get("form_type", ""),
                "filed_at": src.get("file_date", ""),
                "description": src.get("display_names", ""),
                "url": f"https://www.sec.gov/Archives/{src.get('file_date', '')}",
            })
    except Exception:
        pass
    return filings


def fetch_all_news(ticker: str) -> dict[str, Any]:
    """Aggregate news from all available sources."""
    yahoo = fetch_yahoo_news(ticker)
    sec = fetch_sec_filings(ticker)
    return {
        "yahoo_finance": yahoo,
        "sec_filings": sec,
        "total_articles": len(yahoo),
        "total_filings": len(sec),
    }

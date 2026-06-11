"""
Deep web research module — scrapes multiple financial sources for a ticker.
No API keys required; uses public HTML pages and RSS feeds.
"""
from __future__ import annotations

import re
import html
import time
from typing import Any

import requests
from bs4 import BeautifulSoup

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
_TIMEOUT = 12


def _get(url: str, **kwargs) -> requests.Response | None:
    try:
        r = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT, **kwargs)
        r.raise_for_status()
        return r
    except Exception:
        return None


def _text(soup: BeautifulSoup, *selectors) -> str:
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            return el.get_text(strip=True)
    return ""


# ---------------------------------------------------------------------------
# DuckDuckGo HTML search (no API key)
# ---------------------------------------------------------------------------

def _ddg_search(query: str, max_results: int = 8) -> list[dict]:
    """Search DuckDuckGo HTML and return title + snippet + url."""
    results = []
    try:
        r = _get("https://html.duckduckgo.com/html/", params={"q": query, "kl": "us-en"})
        if not r:
            return results
        soup = BeautifulSoup(r.text, "html.parser")
        for item in soup.select(".result")[:max_results]:
            title_el = item.select_one(".result__title")
            snip_el = item.select_one(".result__snippet")
            url_el = item.select_one(".result__url")
            title = title_el.get_text(strip=True) if title_el else ""
            snip = snip_el.get_text(strip=True) if snip_el else ""
            url = url_el.get_text(strip=True) if url_el else ""
            if title:
                results.append({"title": title, "snippet": snip, "url": url})
    except Exception:
        pass
    return results


def search_recent_news(ticker: str, company_name: str = "") -> list[dict]:
    """Search for recent news and analyst commentary."""
    queries = [
        f"{ticker} stock analysis 2025 2026",
        f"{ticker} earnings forecast analyst",
        f"{company_name or ticker} business outlook risks",
    ]
    seen, results = set(), []
    for q in queries:
        for r in _ddg_search(q, max_results=5):
            if r["title"] not in seen:
                seen.add(r["title"])
                results.append(r)
        time.sleep(0.3)
    return results[:15]


def search_bearish_thesis(ticker: str) -> list[dict]:
    """Explicitly search for bear cases and risks."""
    queries = [
        f"{ticker} stock risks overvalued short",
        f"{ticker} problems concerns headwinds",
    ]
    seen, results = set(), []
    for q in queries:
        for r in _ddg_search(q, max_results=5):
            if r["title"] not in seen:
                seen.add(r["title"])
                results.append(r)
        time.sleep(0.3)
    return results[:10]


def search_bullish_thesis(ticker: str) -> list[dict]:
    """Explicitly search for bull cases and catalysts."""
    queries = [
        f"{ticker} stock buy catalyst growth",
        f"{ticker} upside potential long term investment",
    ]
    seen, results = set(), []
    for q in queries:
        for r in _ddg_search(q, max_results=5):
            if r["title"] not in seen:
                seen.add(r["title"])
                results.append(r)
        time.sleep(0.3)
    return results[:10]


# ---------------------------------------------------------------------------
# Finviz snapshot
# ---------------------------------------------------------------------------

def fetch_finviz(ticker: str) -> dict:
    """Scrape Finviz for quick fundamental/technical snapshot."""
    data: dict[str, Any] = {"source": "finviz", "available": False}
    r = _get(f"https://finviz.com/quote.ashx?t={ticker}")
    if not r:
        return data
    soup = BeautifulSoup(r.text, "html.parser")

    # Snapshot table
    table = soup.select_one("table.snapshot-table2") or soup.select_one(".snapshot-table2")
    if table:
        cells = table.find_all("td")
        kvs = {}
        for i in range(0, len(cells) - 1, 2):
            k = cells[i].get_text(strip=True)
            v = cells[i + 1].get_text(strip=True)
            kvs[k] = v
        data.update({
            "available": True,
            "market_cap": kvs.get("Market Cap"),
            "pe": kvs.get("P/E"),
            "forward_pe": kvs.get("Forward P/E"),
            "peg": kvs.get("PEG"),
            "eps_ttm": kvs.get("EPS (ttm)"),
            "eps_next_year": kvs.get("EPS next Y"),
            "sales_growth": kvs.get("Sales Q/Q"),
            "eps_growth_qoq": kvs.get("EPS Q/Q"),
            "insider_own": kvs.get("Insider Own"),
            "short_float": kvs.get("Short Float"),
            "target_price": kvs.get("Target Price"),
            "rsi": kvs.get("RSI (14)"),
            "analyst_recom": kvs.get("Recom"),
            "52w_range": kvs.get("52W Range"),
            "perf_week": kvs.get("Perf Week"),
            "perf_month": kvs.get("Perf Month"),
            "perf_ytd": kvs.get("Perf YTD"),
            "perf_year": kvs.get("Perf Year"),
            "avg_volume": kvs.get("Avg Volume"),
            "rel_volume": kvs.get("Rel Volume"),
            "country": kvs.get("Country"),
            "sector": kvs.get("Sector"),
            "industry": kvs.get("Industry"),
            "debt_eq": kvs.get("Debt/Eq"),
            "roe": kvs.get("ROE"),
            "roa": kvs.get("ROA"),
            "gross_margin": kvs.get("Gross Margin"),
            "oper_margin": kvs.get("Oper. Margin"),
            "profit_margin": kvs.get("Profit Margin"),
            "dividend_yield": kvs.get("Dividend %"),
        })

    # News headlines from Finviz
    news_items = []
    for row in soup.select("table#news-table tr")[:10]:
        cells = row.find_all("td")
        if len(cells) >= 2:
            headline = cells[-1].get_text(strip=True)
            link_el = cells[-1].find("a")
            link = link_el["href"] if link_el and link_el.get("href") else ""
            if headline:
                news_items.append({"headline": headline, "url": link})
    data["recent_headlines"] = news_items

    return data


# ---------------------------------------------------------------------------
# MarketWatch quick news
# ---------------------------------------------------------------------------

def fetch_marketwatch_news(ticker: str) -> list[dict]:
    """Scrape MarketWatch news for a ticker."""
    items = []
    r = _get(f"https://www.marketwatch.com/investing/stock/{ticker.lower()}/news")
    if not r:
        return items
    soup = BeautifulSoup(r.text, "html.parser")
    for article in soup.select("div.article__content")[:10]:
        h3 = article.select_one("h3.article__headline")
        desc = article.select_one("p.article__summary")
        if h3:
            items.append({
                "title": h3.get_text(strip=True),
                "summary": desc.get_text(strip=True) if desc else "",
            })
    return items


# ---------------------------------------------------------------------------
# Google Finance headlines
# ---------------------------------------------------------------------------

def fetch_google_finance_news(ticker: str) -> list[dict]:
    """Fetch Google Finance news headlines for a ticker."""
    items = []
    r = _get(f"https://www.google.com/finance/quote/{ticker}:NASDAQ")
    if not r:
        r = _get(f"https://www.google.com/finance/quote/{ticker}:NYSE")
    if not r:
        return items
    soup = BeautifulSoup(r.text, "html.parser")
    for item in soup.select("div[class*='article']")[:10]:
        title_el = item.find(["h3", "h4", "a"])
        if title_el:
            text = title_el.get_text(strip=True)
            if len(text) > 20:
                items.append({"title": text})
    return items[:8]


# ---------------------------------------------------------------------------
# Macro / industry context search
# ---------------------------------------------------------------------------

def fetch_industry_context(sector: str, industry: str) -> list[dict]:
    """Search for sector/industry macro outlook."""
    if not sector or sector == "N/A":
        return []
    query = f"{sector} {industry} sector outlook 2025 2026 investment"
    return _ddg_search(query, max_results=5)


# ---------------------------------------------------------------------------
# Master deep research function
# ---------------------------------------------------------------------------

def deep_research(ticker: str, company_name: str = "", sector: str = "", industry: str = "") -> dict[str, Any]:
    """
    Run full deep research for a ticker across multiple sources.
    Returns structured findings ready for the ResearchAgent.
    """
    results: dict[str, Any] = {"ticker": ticker, "sources_queried": []}

    # 1. Finviz snapshot
    fv = fetch_finviz(ticker)
    results["finviz"] = fv
    if fv.get("available"):
        results["sources_queried"].append("finviz.com")

    # 2. Recent news search
    news = search_recent_news(ticker, company_name)
    results["web_news"] = news
    if news:
        results["sources_queried"].append("duckduckgo_news_search")

    # 3. Bull / bear thesis searches
    bull_finds = search_bullish_thesis(ticker)
    bear_finds = search_bearish_thesis(ticker)
    results["web_bull_signals"] = bull_finds
    results["web_bear_signals"] = bear_finds

    # 4. MarketWatch
    mw = fetch_marketwatch_news(ticker)
    results["marketwatch_news"] = mw
    if mw:
        results["sources_queried"].append("marketwatch.com")

    # 5. Google Finance
    gf = fetch_google_finance_news(ticker)
    results["google_finance_news"] = gf
    if gf:
        results["sources_queried"].append("google.com/finance")

    # 6. Industry context
    industry_ctx = fetch_industry_context(sector, industry)
    results["industry_context"] = industry_ctx

    # Summary count
    total_sources = len(results["sources_queried"])
    total_items = (
        len(news) + len(bull_finds) + len(bear_finds)
        + len(mw) + len(gf) + len(industry_ctx)
        + len(fv.get("recent_headlines", []))
    )
    results["summary"] = {
        "sources_accessed": total_sources,
        "total_data_points": total_items,
    }

    return results

"""
Research Agent — synthesizes and adversarially verifies web research findings
before they enter the bull/bear analysis pipeline.
"""
from __future__ import annotations

import json
from typing import Any

from scanner.agents.base import call_agent, format_data_for_prompt

SYSTEM_PROMPT = """You are the Research Agent in a multi-agent equities analysis system.

You have received raw web research gathered from multiple sources (DuckDuckGo searches,
Finviz, MarketWatch, Google Finance, industry sources) about a specific equity.

Your job is to:
1. EXTRACT the most material, actionable insights from the raw data
2. VERIFY claims by cross-referencing — flag anything that appears in only one source
3. IDENTIFY contradictions between sources and note them explicitly
4. SEPARATE facts (confirmed numbers, events) from opinions (analyst views, predictions)
5. SURFACE anything surprising, counter-consensus, or high-impact that the market
   may be underweighting in either direction

You must be rigorous and skeptical:
- Do NOT accept a claim as fact unless it appears in at least 2 sources OR comes from
  a primary source (company filing, official announcement)
- Mark unverified claims with [UNVERIFIED]
- Flag potential FUD or hype with [SENTIMENT ONLY]
- If sources contradict each other, present both sides

Structure your response EXACTLY as JSON with these keys:
{
  "verified_facts": [<list of cross-confirmed material facts with source count>],
  "unverified_claims": [<claims seen in only one source — label [UNVERIFIED]>],
  "contradictions": [<where sources disagree — present both sides>],
  "bull_signals_found": [<research-sourced reasons to be bullish with confidence level>],
  "bear_signals_found": [<research-sourced reasons to be bearish with confidence level>],
  "industry_macro_context": <2-3 sentence summary of sector/industry backdrop>,
  "sentiment_tone": <"strongly bullish" | "mildly bullish" | "neutral" | "mildly bearish" | "strongly bearish">,
  "most_important_finding": <the single most impactful thing the research surfaced>,
  "data_quality_note": <assessment of how complete and reliable this research is>,
  "sources_used": <integer count of sources that returned data>
}

Only output valid JSON, no markdown fences."""


def analyze(ticker: str, research_data: dict[str, Any], fundamentals: dict[str, Any]) -> dict:
    """Synthesize and verify web research findings."""

    # Build a focused prompt from the raw research
    company = fundamentals.get("name", ticker)
    sector = fundamentals.get("sector", "N/A")
    industry = fundamentals.get("industry", "N/A")

    # Compress finviz data for prompt
    fv = research_data.get("finviz", {})
    finviz_snapshot = {k: v for k, v in fv.items()
                       if k not in ("available", "source") and v and v != "N/A"} if fv.get("available") else {}

    prompt = f"""Research report for {ticker} ({company}) — {sector} / {industry}

=== FINVIZ SNAPSHOT ===
{json.dumps(finviz_snapshot, indent=2)}

=== FINVIZ RECENT HEADLINES ===
{json.dumps(fv.get('recent_headlines', []), indent=2)}

=== WEB NEWS SEARCH RESULTS ===
{json.dumps(research_data.get('web_news', [])[:10], indent=2)}

=== WEB BULL SIGNAL SEARCHES ===
{json.dumps(research_data.get('web_bull_signals', [])[:8], indent=2)}

=== WEB BEAR SIGNAL SEARCHES ===
{json.dumps(research_data.get('web_bear_signals', [])[:8], indent=2)}

=== MARKETWATCH HEADLINES ===
{json.dumps(research_data.get('marketwatch_news', [])[:8], indent=2)}

=== GOOGLE FINANCE NEWS ===
{json.dumps(research_data.get('google_finance_news', [])[:6], indent=2)}

=== INDUSTRY / MACRO CONTEXT ===
{json.dumps(research_data.get('industry_context', [])[:5], indent=2)}

Sources accessed: {research_data.get('summary', {}).get('sources_accessed', 0)}
Total data points: {research_data.get('summary', {}).get('total_data_points', 0)}

Synthesize, verify, and flag everything above. Return valid JSON only."""

    raw = call_agent(SYSTEM_PROMPT, prompt, max_tokens=3000)
    try:
        return json.loads(raw)
    except Exception:
        return {
            "verified_facts": [],
            "bull_signals_found": [],
            "bear_signals_found": [],
            "sentiment_tone": "neutral",
            "most_important_finding": raw[:300],
            "data_quality_note": "JSON parse failed",
            "error": "JSON parse failed",
            "_raw": raw,
        }

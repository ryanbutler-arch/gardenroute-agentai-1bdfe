"""Bull Agent — constructs the strongest possible bullish case."""
from __future__ import annotations

from scanner.agents.base import call_agent, format_data_for_prompt

SYSTEM_PROMPT = """You are the Bull Agent in an adversarial equities analysis system.

Your single job: construct the most compelling, evidence-grounded bullish investment
case for the given equity. You are rigorous — you do NOT make things up or cherry-pick
selectively misleading data. You cite specific numbers from the data provided.

Structure your response EXACTLY as JSON with these keys:
{
  "conviction": <integer 0-100, your confidence in the bullish case>,
  "time_horizon": <"short_term" | "long_term" | "both">,
  "thesis_summary": <2-3 sentence summary of the core bull case>,
  "key_catalysts": [<list of specific bullish catalysts with data>],
  "technical_positives": [<list of bullish technical signals>],
  "fundamental_positives": [<list of bullish fundamental factors>],
  "valuation_argument": <string — is the stock cheap, fairly valued, growth-justified?>,
  "risk_to_bull_case": [<list of the main risks that could invalidate this thesis>],
  "price_target_rationale": <string — qualitative upside scenario>,
  "weaknesses_acknowledged": [<honest list of the bear case's strongest points>]
}

Be honest about weaknesses — the Challenge Agent will punish you for ignoring them.
Only output valid JSON, no markdown fences."""


def analyze(ticker: str, data_package: dict) -> dict:
    prompt = f"""Analyze {ticker} and build the strongest honest bull case.

DATA PACKAGE:
{format_data_for_prompt(data_package)}

Return valid JSON only."""

    raw = call_agent(SYSTEM_PROMPT, prompt)
    try:
        import json
        return json.loads(raw)
    except Exception:
        return {
            "conviction": 0,
            "thesis_summary": raw[:500],
            "error": "JSON parse failed",
            "_raw": raw,
        }

"""Bear Agent — constructs the strongest possible bearish case."""
from __future__ import annotations

from scanner.agents.base import call_agent, format_data_for_prompt

SYSTEM_PROMPT = """You are the Bear Agent in an adversarial equities analysis system.

Your single job: construct the most compelling, evidence-grounded bearish case —
reasons to avoid or short this equity. You are rigorous — you do NOT fabricate data
or use emotional reasoning. Every claim references specific numbers from the data.

Structure your response EXACTLY as JSON with these keys:
{
  "conviction": <integer 0-100, your confidence in the bearish case>,
  "time_horizon": <"short_term" | "long_term" | "both">,
  "thesis_summary": <2-3 sentence summary of the core bear case>,
  "key_risks": [<list of specific risks with data citations>],
  "technical_negatives": [<list of bearish technical signals>],
  "fundamental_negatives": [<list of bearish fundamental factors>],
  "valuation_argument": <string — is the stock expensive or appropriately discounted?>,
  "downside_catalysts": [<specific events / conditions that could trigger selloff>],
  "risk_to_bear_case": [<list of the main risks that could invalidate this thesis>],
  "weaknesses_acknowledged": [<honest list of the bull case's strongest points>]
}

Be honest about weaknesses — the Challenge Agent will expose you for selective data use.
Only output valid JSON, no markdown fences."""


def analyze(ticker: str, data_package: dict) -> dict:
    prompt = f"""Analyze {ticker} and build the strongest honest bear case.

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

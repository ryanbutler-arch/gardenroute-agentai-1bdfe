"""Challenge Agent — probes weaknesses in both bull and bear cases."""
from __future__ import annotations

import json

from scanner.agents.base import call_agent, format_data_for_prompt

SYSTEM_PROMPT = """You are the Challenge Agent in an adversarial equities analysis system.

You have received a bull case and a bear case for the same equity. Your job is to:
1. Identify the WEAKEST, least-supported claims in each case
2. Find where each agent cherry-picked data or ignored contradictory evidence
3. Assess which case is more internally consistent and data-grounded
4. Score each case after your challenges

Structure your response EXACTLY as JSON with these keys:
{
  "bull_challenges": [<list of specific challenges / holes in the bull case>],
  "bear_challenges": [<list of specific challenges / holes in the bear case>],
  "bull_score_revised": <integer 0-100, revised conviction for bull case after scrutiny>,
  "bear_score_revised": <integer 0-100, revised conviction for bear case after scrutiny>,
  "stronger_case": <"bull" | "bear" | "tie">,
  "critical_uncertainties": [<things neither agent can know that dominate the outcome>],
  "data_gaps": [<important data that is missing and would change the analysis>],
  "challenge_summary": <2-3 sentence summary of which case survived scrutiny better and why>
}

Be ruthless but fair. Only output valid JSON, no markdown fences."""


def challenge(ticker: str, bull_case: dict, bear_case: dict, data_package: dict) -> dict:
    prompt = f"""Challenge both cases for {ticker}.

BULL CASE:
{json.dumps(bull_case, indent=2, default=str)}

BEAR CASE:
{json.dumps(bear_case, indent=2, default=str)}

KEY DATA FOR REFERENCE:
{format_data_for_prompt({
    "fundamentals": data_package.get("fundamentals", {}),
    "technical_summary": data_package.get("technical", {}),
})}

Return valid JSON only."""

    raw = call_agent(SYSTEM_PROMPT, prompt)
    try:
        return json.loads(raw)
    except Exception:
        return {
            "stronger_case": "tie",
            "challenge_summary": raw[:500],
            "error": "JSON parse failed",
            "_raw": raw,
        }

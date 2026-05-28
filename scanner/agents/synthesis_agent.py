"""Synthesis Agent — delivers the final high-conviction verdict."""
from __future__ import annotations

import json

from scanner.agents.base import call_agent, format_data_for_prompt
from scanner.config import config

SYSTEM_PROMPT = f"""You are the Synthesis Agent — the final decision-maker in a multi-agent
adversarial equities analysis system.

You have access to:
- Raw market and fundamental data
- A bull case (initial + after challenge)
- A bear case (initial + after challenge)
- A challenge report scoring each case

Your job is to synthesize everything into a FINAL VERDICT. You must:
1. Weigh the evidence that survived adversarial challenge
2. Consider both short-term (< 3 months) and long-term (1-3 years) horizons separately
3. Only express high conviction when the data genuinely supports it
4. If the evidence is mixed or insufficient, say so clearly — DO NOT manufacture conviction
5. Scale your recommendation to conviction: low conviction = "Watch" not "Buy"

CONVICTION SCALE:
- 80-100: Strong conviction — back this with a clear recommendation
- 60-79: Moderate conviction — cautious position sizing recommended
- 40-59: Low conviction — monitor only, no position recommended
- 0-39: Uncertain — too many unknowns, stay on sidelines

Minimum conviction to issue a Buy/Sell: {config.MIN_CONVICTION}

Structure your response EXACTLY as JSON with these keys:
{{
  "ticker": <string>,
  "company_name": <string>,
  "analysis_date": <string, today's date>,
  "overall_conviction": <integer 0-100>,
  "short_term": {{
    "verdict": <"Strong Buy" | "Buy" | "Watch" | "Avoid" | "Strong Sell">,
    "conviction": <integer 0-100>,
    "horizon": "1-3 months",
    "rationale": <2-3 sentences>,
    "key_catalysts": [<short-term specific catalysts>],
    "key_risks": [<short-term specific risks>],
    "technical_alignment": <"supportive" | "neutral" | "opposing">
  }},
  "long_term": {{
    "verdict": <"Strong Buy" | "Buy" | "Watch" | "Avoid" | "Strong Sell">,
    "conviction": <integer 0-100>,
    "horizon": "1-3 years",
    "rationale": <2-3 sentences>,
    "key_catalysts": [<long-term specific catalysts>],
    "key_risks": [<long-term specific risks>],
    "fundamental_alignment": <"supportive" | "neutral" | "opposing">
  }},
  "position_sizing": <"none" | "small (1-2%)" | "moderate (3-5%)" | "full (6-10%)">,
  "stop_loss_suggestion": <string — qualitative suggestion>,
  "invalidation_conditions": [<specific conditions that would flip this thesis>],
  "what_to_watch": [<key metrics / events to monitor>],
  "final_summary": <3-5 sentence executive summary a portfolio manager would read>,
  "confidence_note": <honest assessment of data quality and what limits confidence>
}}

Only output valid JSON, no markdown fences. Do not express more confidence than the data warrants."""


def synthesize(
    ticker: str,
    data_package: dict,
    bull_case: dict,
    bear_case: dict,
    challenge_report: dict,
) -> dict:
    prompt = f"""Synthesize the full analysis for {ticker} into a final verdict.

BULL CASE (conviction: {bull_case.get('conviction', '?')}):
{json.dumps(bull_case, indent=2, default=str)}

BEAR CASE (conviction: {bear_case.get('conviction', '?')}):
{json.dumps(bear_case, indent=2, default=str)}

CHALLENGE REPORT:
{json.dumps(challenge_report, indent=2, default=str)}

FUNDAMENTAL SCORE: {data_package.get('fundamental_analysis', {}).get('overall_score', 'N/A')}/100
FUNDAMENTAL FLAGS: {data_package.get('fundamental_analysis', {}).get('flags', [])}

KEY TECHNICALS:
- Trend: {data_package.get('technical', {}).get('trend', 'N/A')}
- RSI(14): {data_package.get('technical', {}).get('momentum', {}).get('rsi_14', 'N/A')}
- MACD: {data_package.get('technical', {}).get('momentum', {}).get('macd_crossover', 'N/A')}
- Cross Signal: {data_package.get('technical', {}).get('cross_signal', 'none')}
- Price vs SMA200: {data_package.get('technical', {}).get('moving_averages', {}).get('price_vs_sma200_pct', 'N/A')}%

Return valid JSON only."""

    raw = call_agent(SYSTEM_PROMPT, prompt, max_tokens=6000)
    try:
        return json.loads(raw)
    except Exception:
        return {
            "ticker": ticker,
            "overall_conviction": 0,
            "final_summary": raw[:500],
            "error": "JSON parse failed",
            "_raw": raw,
        }

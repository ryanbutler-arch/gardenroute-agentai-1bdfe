"""Central configuration and environment loading."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")


class Config:
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ALPHA_VANTAGE_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    FMP_KEY: str = os.getenv("FMP_API_KEY", "")
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")

    # Claude model to use for agents
    CLAUDE_MODEL: str = "claude-sonnet-4-6"

    # Analysis windows
    SHORT_TERM_DAYS: int = 90
    LONG_TERM_DAYS: int = 365 * 3

    # Agent temperature — lower = more deterministic / high-confidence only
    AGENT_TEMPERATURE: float = 0.2

    # How many challenge rounds each pair of agents runs
    CHALLENGE_ROUNDS: int = 2

    # Minimum conviction score (0-100) required before a verdict is reported
    MIN_CONVICTION: int = 60

    @classmethod
    def validate(cls) -> None:
        if not cls.ANTHROPIC_API_KEY:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY is not set. "
                "Copy .env.example to .env and add your key."
            )


config = Config()

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    es_url: str
    es_api_key: str = field(repr=False)
    es_index: str
    inference_id: str
    openai_api_key: str = field(repr=False)
    openai_model: str
    timeout: float = 60


def load_settings(require_openai: bool = True) -> Settings:
    load_dotenv(ROOT / ".env", override=False)
    required = ["ES_URL", "ES_API_KEY", "ES_INFERENCE_ID"]
    if require_openai:
        required.append("OPENAI_API_KEY")
    missing = [name for name in required if not os.getenv(name, "").strip()]
    if missing:
        raise ValueError("Set these values in .env: " + ", ".join(missing))
    index = os.getenv("ES_INDEX", "shopping-demo-products")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", index):
        raise ValueError(
            "ES_INDEX must be a single lowercase index name; wildcards are disallowed."
        )
    url = os.getenv("ES_URL", "").strip()
    if not url.startswith("https://") or "YOUR-PROJECT" in url:
        raise ValueError("ES_URL must be your real HTTPS Elasticsearch project endpoint.")
    timeout = float(os.getenv("REQUEST_TIMEOUT", "60"))
    if not 1 <= timeout <= 300:
        raise ValueError("REQUEST_TIMEOUT must be between 1 and 300 seconds.")
    return Settings(
        url,
        os.environ["ES_API_KEY"],
        index,
        os.environ["ES_INFERENCE_ID"],
        os.getenv("OPENAI_API_KEY", ""),
        os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        timeout,
    )

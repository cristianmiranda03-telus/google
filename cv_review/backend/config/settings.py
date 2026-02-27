"""Load settings from config.yaml and environment."""
import os
from pathlib import Path

import yaml

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"
SKILL_MATRIX_PATH = Path(__file__).resolve().parent / "skill_matrix.yaml"


def _load_yaml(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_settings():
    """Return merged settings from YAML and env."""
    cfg = _load_yaml(CONFIG_PATH)
    api = cfg.get("api") or {}
    api_key = os.getenv("FUELIX_API_KEY", os.getenv("FUELIX_SECRET_TOKEN", ""))
    model = os.getenv("FUELIX_MODEL", api.get("model", "gemini-3-pro"))
    fast_model = os.getenv("FUELIX_FAST_MODEL", api.get("fast_model", "gemini-2.0-flash"))
    return {
        "api": {
            **api,
            "base_url": os.getenv("FUELIX_BASE_URL", api.get("base_url", "https://api.fuelix.ai/v1")),
            "model": model,
            "fast_model": fast_model,
        },
        "api_key": api_key,
        "evaluation": cfg.get("evaluation") or {},
        "app": cfg.get("app") or {},
    }


def get_skill_matrix():
    """Return full skill matrix (areas -> specializations -> skills)."""
    return _load_yaml(SKILL_MATRIX_PATH)

"""Resources package — static prompts, knowledge bases, and configs."""

from pathlib import Path

RESOURCES_DIR = Path(__file__).parent

PROMPTS_DIR = RESOURCES_DIR / "prompts"
KB_DIR = RESOURCES_DIR / "knowledge_base"
CONFIGS_DIR = RESOURCES_DIR / "configs"


def load_prompt(name: str) -> str:
    """Load a prompt template by filename (without extension)."""
    path = PROMPTS_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8")

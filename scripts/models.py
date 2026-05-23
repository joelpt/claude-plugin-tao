#!/usr/bin/env python3
"""Display the tao model configuration from config/models.json.

Usage:
  python3 models.py [--config=<path>]

Reads model assignments and prints a human-readable table of provider,
model, and role for each configured voice.
"""

import argparse
import json
from pathlib import Path


_DEFAULT_CONFIG = Path(__file__).parent.parent / "config" / "models.json"


def load_config(config_path: Path) -> dict[str, object]:
    """Load and return the models.json config.

    Args:
        config_path: Path to the models.json file.

    Returns:
        Parsed config dict.
    """
    with config_path.open() as f:
        return json.load(f)  # type: ignore[no-any-return]


def print_table(config: dict[str, object]) -> None:
    """Print a human-readable table of model assignments.

    Args:
        config: Parsed models.json dict.
    """
    default_local = config.get("_default_local_model", "(not set)")
    print(f"Default local model: {default_local}\n")

    header = f"{'Mode':<12} {'Role':<12} {'Provider':<10} {'Model':<20}"
    print(header)
    print("-" * len(header))

    for section, value in config.items():
        if section.startswith("_"):
            continue
        if not isinstance(value, dict):
            continue
        for role, entry in value.items():
            if not isinstance(entry, dict):
                continue
            provider = entry.get("provider", "?")
            model = entry.get("model") or (
                default_local if provider == "ollama" else "default"
            )
            print(f"{section:<12} {role:<12} {provider:<10} {model:<20}")


def main() -> None:
    """Parse arguments and print the model configuration table."""
    parser = argparse.ArgumentParser(description="Show tao model assignments")
    parser.add_argument(
        "--config",
        default=str(_DEFAULT_CONFIG),
        help="Path to models.json (default: config/models.json relative to repo root)",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"ERROR: config not found at {config_path}")
        raise SystemExit(1)

    config = load_config(config_path)
    print_table(config)


if __name__ == "__main__":
    main()

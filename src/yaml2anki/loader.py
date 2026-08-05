import sys

import yaml


def load_flashcards(yaml_path: str) -> dict:
    """Load and validate flashcard YAML structure."""
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if (
                not isinstance(data, dict)
                or "deck_name" not in data
                or "cards" not in data
            ):
                raise ValueError("YAML must contain 'deck_name' and 'cards' keys.")
            return data
    except Exception as e:
        print(f"Error loading YAML file: {e}")
        sys.exit(1)

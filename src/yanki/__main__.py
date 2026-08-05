import argparse
import random
import sys

import genanki
import requests
import yaml

DEFAULT_ANKI_CONNECT_URL = "http://localhost:8765"

DEFAULT_CSS = """
.card {
    font-family: arial;
    font-size: 20px;
    text-align: center;
    color: black;
    background-color: white;
}
"""

DEFAULT_QFMT = "{{Front}}"
DEFAULT_AFMT = '{{Front}}<hr id="answer">{{Back}}'


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


def build_genanki_model(deck_name: str, styling: dict) -> genanki.Model:
    """Dynamically construct a genanki Model based on user styling or defaults."""
    model_id = random.Random(deck_name + "_model").randint(1000000000, 2000000000)

    css = styling.get("css", DEFAULT_CSS)
    qfmt = styling.get("front_template", DEFAULT_QFMT)
    afmt = styling.get("back_template", DEFAULT_AFMT)

    return genanki.Model(
        model_id,
        f"Yanki Model ({deck_name})",
        fields=[
            {"name": "Front"},
            {"name": "Back"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": qfmt,
                "afmt": afmt,
            },
        ],
        css=css,
    )


def generate_apkg(data: dict, output_path: str) -> None:
    """Generate a .apkg file using genanki with custom styling."""
    deck_name = data["deck_name"]
    deck_id = random.Random(deck_name).randint(1000000000, 2000000000)

    styling = data.get("styling", {})
    model = build_genanki_model(deck_name, styling)
    deck = genanki.Deck(deck_id, deck_name)

    for card in data.get("cards", []):
        front = card.get("front", "")
        back = card.get("back", "")
        tags = card.get("tags", [])

        note = genanki.Note(
            model=model,
            fields=[str(front), str(back)],
            tags=tags if isinstance(tags, list) else [tags],
        )
        deck.add_note(note)

    genanki.Package(deck).write_to_file(output_path)
    print(f"Successfully generated package: {output_path}")


def import_to_ankiconnect(data: dict, url: str = DEFAULT_ANKI_CONNECT_URL) -> None:
    """Import cards via AnkiConnect, creating/updating a custom model if requested."""
    deck_name = data["deck_name"]
    styling = data.get("styling", {})

    def invoke(action, **params):
        response = requests.post(
            url, json={"action": action, "version": 6, "params": params}
        ).json()
        if response.get("error") is not None:
            raise Exception(response["error"])
        return response.get("result")

    try:
        invoke("createDeck", deck=deck_name)

        model_name = f"Yanki - {deck_name}"
        existing_models = invoke("modelNames")

        # Create or update the custom note type in Anki
        if model_name not in existing_models:
            invoke(
                "createModel",
                modelName=model_name,
                inOrderFields=["Front", "Back"],
                css=styling.get("css", DEFAULT_CSS),
                cardTemplates=[
                    {
                        "Name": "Card 1",
                        "Front": styling.get("front_template", DEFAULT_QFMT),
                        "Back": styling.get("back_template", DEFAULT_AFMT),
                    }
                ],
            )
        elif "styling" in data:
            # Update existing model CSS/templates if provided
            invoke(
                "updateModelStyling",
                model={"name": model_name, "css": styling.get("css", DEFAULT_CSS)},
            )
            invoke(
                "updateModelTemplates",
                model={
                    "name": model_name,
                    "templates": {
                        "Card 1": {
                            "Front": styling.get("front_template", DEFAULT_QFMT),
                            "Back": styling.get("back_template", DEFAULT_AFMT),
                        }
                    },
                },
            )

        notes = []
        for card in data.get("cards", []):
            notes.append(
                {
                    "deckName": deck_name,
                    "modelName": model_name,
                    "fields": {
                        "Front": str(card.get("front", "")),
                        "Back": str(card.get("back", "")),
                    },
                    "tags": card.get("tags", []),
                }
            )

        result = invoke("addNotes", notes=notes)
        added_count = sum(1 for n in result if n is not None)
        print(
            f"Successfully imported {added_count}/{len(notes)} cards into deck '{deck_name}'."
        )

    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to AnkiConnect. Ensure Anki is running.")
        sys.exit(1)
    except Exception as e:
        print(f"AnkiConnect Error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Yanki: YAML to Anki converter with custom styling"
    )
    parser.add_argument("yaml_file", help="Path to input YAML file")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-o", "--output", help="Output .apkg file path")
    group.add_argument(
        "-i",
        "--import-direct",
        action="store_true",
        help="Import directly via AnkiConnect",
    )

    parser.add_argument(
        "--url", default=DEFAULT_ANKI_CONNECT_URL, help="AnkiConnect API URL"
    )

    args = parser.parse_args()
    data = load_flashcards(args.yaml_file)

    if args.output:
        generate_apkg(data, args.output)
    elif args.import_direct:
        import_to_ankiconnect(data, args.url)


if __name__ == "__main__":
    main()

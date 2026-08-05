import argparse
import random
import sys

import genanki
import requests
import yaml

DEFAULT_ANKI_CONNECT_URL = "http://localhost:8765"


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
                raise ValueError("YAML must contain 'deck_name' and 'cards' key.")
            return data
    except Exception as e:
        print(f"Error loading YAML file: {e}")
        sys.exit(1)


def generate_apkg(data: dict, output_path: str) -> None:
    """Generate a .apkg file using genanki."""
    # Generate stable pseudo-random IDs based on deck/model name
    deck_id = random.Random(data["deck_name"]).randint(1000000000, 2000000000)
    model_id = random.Random(data["deck_name"] + "_model").randint(
        1000000000, 2000000000
    )

    model = genanki.Model(
        model_id,
        "Yanki Basic Model",
        fields=[
            {"name": "Front"},
            {"name": "Back"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{Front}}",
                "afmt": '{{Front}}<hr id="answer">{{Back}}',
            },
        ],
    )

    deck = genanki.Deck(deck_id, data["deck_name"])

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
    """Directly import cards into a running Anki instance via AnkiConnect."""
    deck_name = data["deck_name"]

    def invoke(action, **params):
        response = requests.post(
            url, json={"action": action, "version": 6, "params": params}
        ).json()
        if len(response) != 2:
            raise Exception("Response has an unexpected number of fields")
        if "error" not in response or "result" not in response:
            raise Exception("Response is missing required fields")
        if response["error"] is not None:
            raise Exception(response["error"])
        return response["result"]

    try:
        # Create deck if it doesn't exist
        invoke("createDeck", deck=deck_name)

        # Prepare notes
        notes = []
        for card in data.get("cards", []):
            notes.append(
                {
                    "deckName": deck_name,
                    "modelName": "Basic",
                    "fields": {
                        "Front": str(card.get("front", "")),
                        "Back": str(card.get("back", "")),
                    },
                    "tags": card.get("tags", []),
                }
            )

        # Add notes
        result = invoke("addNotes", notes=notes)
        added_count = sum(1 for n in result if n is not None)
        print(
            f"Successfully imported {added_count}/{len(notes)} cards into deck '{deck_name}'."
        )

    except requests.exceptions.ConnectionError:
        print(
            "Error: Could not connect to AnkiConnect. Make sure Anki is running and AnkiConnect is installed."
        )
        sys.exit(1)
    except Exception as e:
        print(f"AnkiConnect Error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Yanki: YAML to Anki flashcard converter/importer"
    )
    parser.add_argument("yaml_file", help="Path to input YAML file")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-o", "--output", help="Output .apkg file path")
    group.add_argument(
        "-i",
        "--import-direct",
        action="store_true",
        help="Import directly into Anki via AnkiConnect",
    )

    parser.add_argument(
        "--url",
        default=DEFAULT_ANKI_CONNECT_URL,
        help="AnkiConnect API URL (default: http://localhost:8765)",
    )

    args = parser.parse_args()
    data = load_flashcards(args.yaml_file)

    if args.output:
        generate_apkg(data, args.output)
    elif args.import_direct:
        import_to_ankiconnect(data, args.url)


if __name__ == "__main__":
    main()

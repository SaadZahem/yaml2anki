import random

import genanki

from . import defaults


def build_genanki_model(deck_name: str, styling: dict) -> genanki.Model:
    """Dynamically construct a genanki Model based on user styling or defaults."""
    model_id = random.Random(deck_name + "_model").randint(1000000000, 2000000000)

    css = styling.get("css", defaults.DEFAULT_CSS)
    qfmt = styling.get("front_template", defaults.DEFAULT_QFMT)
    afmt = styling.get("back_template", defaults.DEFAULT_AFMT)

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

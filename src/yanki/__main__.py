import argparse
import pathlib
import random
import string
import sys

import genanki
import requests
import yaml
from weasyprint import HTML

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

package_dir = pathlib.Path(__file__).parent
PRINT_TEMPLATE_HTML = string.Template((package_dir / "print_template.html").read_text())


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


def render_printable_html(data: dict) -> str:
    deck_name = data.get("deck_name", "Flashcards")
    cards = data.get("cards", [])
    styling = data.get("styling", {})
    custom_css = styling.get("css", "")

    cards_per_page = 8
    cols = 2

    front_rows_html = []
    back_rows_html = []

    for i in range(0, len(cards), cards_per_page):
        page_cards = cards[i : i + cards_per_page]

        for row_idx in range(0, len(page_cards), cols):
            row_cards = page_cards[row_idx : row_idx + cols]

            # Front Row
            f_row = ["<tr>"]
            for idx, c in enumerate(row_cards):
                card_num = i + row_idx + idx + 1
                tags = c.get("tags", [])
                tag_str = (
                    tags[0]
                    if isinstance(tags, list) and tags
                    else (tags if isinstance(tags, str) else "")
                )
                tag_html = (
                    f'<span class="tag-badge">{tag_str}</span>' if tag_str else ""
                )

                f_cell = (
                    '<td class="card-cell">'
                    '<div class="card-box">'
                    f'<span class="card-num">#{card_num}</span>'
                    f"{tag_html}"
                    '<div class="card-section-label">Front / Question</div>'
                    f'<div class="card-content">{c.get("front", "")}</div>'
                    "</div>"
                    "</td>"
                )
                f_row.append(f_cell)
            if len(row_cards) < cols:
                f_row.append('<td class="card-cell"></td>')
            f_row.append("</tr>")
            front_rows_html.append("".join(f_row))

            # Back Row (Horizontally mirrored for two-sided alignment)
            b_row = ["<tr>"]
            mirrored_cards = list(reversed(row_cards))
            for idx, c in enumerate(mirrored_cards):
                orig_idx = len(row_cards) - 1 - idx
                card_num = i + row_idx + orig_idx + 1
                tags = c.get("tags", [])
                tag_str = (
                    tags[0]
                    if isinstance(tags, list) and tags
                    else (tags if isinstance(tags, str) else "")
                )
                tag_html = (
                    f'<span class="tag-badge">{tag_str}</span>' if tag_str else ""
                )

                b_cell = (
                    '<td class="card-cell">'
                    '<div class="card-box">'
                    f'<span class="card-num">#{card_num}</span>'
                    f"{tag_html}"
                    '<div class="card-section-label">Back / Answer</div>'
                    f'<div class="card-content">{c.get("back", "")}</div>'
                    "</div>"
                    "</td>"
                )
                b_row.append(b_cell)
            if len(row_cards) < cols:
                b_row.insert(1, '<td class="card-cell"></td>')
            b_row.append("</tr>")
            back_rows_html.append("".join(b_row))

    return PRINT_TEMPLATE_HTML.safe_substitute(
        deck_name=deck_name,
        custom_css=custom_css,
        front_rows="\n".join(front_rows_html),
        back_rows="\n".join(back_rows_html),
    )


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


def generate_pdf(data: dict, output_pdf_path: str):
    html_content = render_printable_html(data)
    HTML(string=html_content).write_pdf(output_pdf_path)
    print(f"Successfully generated printable PDF: {output_pdf_path}")


def generate_html(data: dict, output_html_path: str):
    html_content = render_printable_html(data)
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Successfully generated printable HTML: {output_html_path}")


def main():
    parser = argparse.ArgumentParser(
        prog="yanki", description="Yanki: Create Anki flashcards from YAML"
    )
    parser.add_argument("yaml_file", help="Path to input YAML file")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-o", "--output", help="Output .apkg file path")
    group.add_argument(
        "-i",
        "--import",
        action="store_true",
        help="Import to anki via AnkiConnect",
    )
    group.add_argument("--pdf", help="Output printable PDF file path")
    group.add_argument("--html", help="Output printable HTML file path")
    parser.add_argument(
        "--url", default=DEFAULT_ANKI_CONNECT_URL, help="AnkiConnect API URL"
    )

    if len(sys.argv) == 1:
        parser.print_help()
        exit(0)

    args = parser.parse_args()
    data = load_flashcards(args.yaml_file)

    if args.output:
        generate_apkg(data, args.output)
    elif args.import_direct:
        import_to_ankiconnect(data, args.url)
    elif args.pdf:
        generate_pdf(data, args.pdf)
    elif args.html:
        generate_html(data, args.html)


if __name__ == "__main__":
    main()

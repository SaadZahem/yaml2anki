import sys

import requests

from . import defaults


def import_to_ankiconnect(
    data: dict, url: str = defaults.DEFAULT_ANKI_CONNECT_URL
) -> None:
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
                css=styling.get("css", defaults.DEFAULT_CSS),
                cardTemplates=[
                    {
                        "Name": "Card 1",
                        "Front": styling.get("front_template", defaults.DEFAULT_QFMT),
                        "Back": styling.get("back_template", defaults.DEFAULT_AFMT),
                    }
                ],
            )
        elif "styling" in data:
            # Update existing model CSS/templates if provided
            invoke(
                "updateModelStyling",
                model={
                    "name": model_name,
                    "css": styling.get("css", defaults.DEFAULT_CSS),
                },
            )
            invoke(
                "updateModelTemplates",
                model={
                    "name": model_name,
                    "templates": {
                        "Card 1": {
                            "Front": styling.get(
                                "front_template", defaults.DEFAULT_QFMT
                            ),
                            "Back": styling.get("back_template", defaults.DEFAULT_AFMT),
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

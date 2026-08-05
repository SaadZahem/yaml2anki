import argparse

from . import defaults


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self):
        super().__init__(
            prog="yaml2anki",
            description="Create anki flashcards from YAML.",
        )

        self.add_argument("yaml_file", help="Path to input YAML file")

        group = self.add_mutually_exclusive_group(required=True)
        group.add_argument("-o", "--output", help="Output .apkg file path")
        group.add_argument(
            "-i",
            "--import-direct",
            action="store_true",
            help="Import to anki via AnkiConnect",
        )
        group.add_argument("--pdf", help="Output printable PDF file path")
        group.add_argument("--html", help="Output printable HTML file path")
        self.add_argument(
            "--url",
            default=defaults.DEFAULT_ANKI_CONNECT_URL,
            help="AnkiConnect API URL",
        )

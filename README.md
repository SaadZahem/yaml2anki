# yaml2anki

[![PyPI Version](https://img.shields.io/pypi/v/yaml2anki.svg)](https://pypi.org/project/yaml2anki/)
[![Python Versions](https://img.shields.io/pypi/pyversions/yaml2anki.svg)](https://pypi.org/project/yaml2anki/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/SaadZahem/yaml2anki/actions/workflows/publish.yml/badge.svg)](https://github.com/SaadZahem/yaml2anki/actions)

YAML to Anki converter and printable flashcard generator.

## Installation

Install using [uv](https://docs.astral.sh/uv/):

    uv tool install yaml2anki

Install using pip:

    pip install yaml2anki

## Usage

The program takes up a YAML file of [a specific format](#input-file-format) and does one of the following actions.

1. [Create .apkg file](#apkg)
2. [Import to anki via AnkiConnect](#import-to-anki)
3. [Generate a printable document of flashcards](#print)

## input file format

The following is a simple example of a valid YAML file.

```yaml
deck_name: "Python Basics"
cards:
  - front: "What is a `list` in Python?"
    back: "An ordered, mutable sequence of elements."
    tags: ["python", "data-structures"]

  - front: "How do you define a function?"
    back: "Using the <code>def</code> keyword."
    tags: ["python", "syntax"]
```

Refer to [examples](https://github.com/SaadZahem/yaml2anki/tree/main/examples) folder for more examples.

### apkg

The following command will generate a .apkg file in the current directory.

    uvx yaml2anki mydeck.yaml -o mydeck.apkg

### import to anki

This option requires installation of [AnkiConnect](https://ankiweb.net/shared/info/2055492159) as an add-on.
After installation of the add-on, close the app and launch it again so that changes can take effect.
While anki instance is running, run the following command

    uvx yaml2anki mydeck.yaml -i

### print

The following command will generate a pdf file in the current directory.

    uvx yaml2anki mydeck.yaml --pdf output.pdf

The pdf document should have an even number of pages where front and back of flashcards meet each other.
After printing the document, you can cut the cards around the dashed lines to get your physical cards.
Similarly, the following command generates a printable html document.

    uvx yaml2anki mydeck.yaml --html output.html

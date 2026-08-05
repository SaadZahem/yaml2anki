import sys

from . import cli
from .apkg import generate_apkg
from .importer import import_to_ankiconnect
from .loader import load_flashcards
from .printer import Printer


def main():
    parser = cli.ArgumentParser()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    data = load_flashcards(args.yaml_file)

    if args.output:
        generate_apkg(data, args.output)
    elif args.import_direct:
        import_to_ankiconnect(data, args.url)
    elif args.pdf:
        Printer(data).generate_pdf(args.pdf)
    elif args.html:
        Printer(data).generate_html(args.html)


if __name__ == "__main__":
    main()

from weasyprint import HTML

from . import defaults


class Printer:
    def __init__(self, data: dict):
        self.html_content = self._render_printable_html(data)

    def generate_pdf(self, output_pdf_path: str):
        HTML(string=self.html_content).write_pdf(output_pdf_path)
        print(f"Successfully generated printable PDF: {output_pdf_path}")

    def generate_html(self, output_html_path: str):
        with open(output_html_path, "w", encoding="utf-8") as f:
            f.write(self.html_content)
        print(f"Successfully generated printable HTML: {output_html_path}")

    @staticmethod
    def _render_printable_html(data: dict) -> str:
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

        return defaults.PRINT_TEMPLATE_HTML.safe_substitute(
            deck_name=deck_name,
            base_css=defaults.PRINT_CSS,
            custom_css=custom_css,
            front_rows="\n".join(front_rows_html),
            back_rows="\n".join(back_rows_html),
        )

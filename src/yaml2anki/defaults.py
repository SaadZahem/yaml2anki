import pathlib
import string

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
PRINT_CSS = (package_dir / "print_styles.css").read_text()
PRINT_TEMPLATE_HTML = string.Template((package_dir / "print_template.html").read_text())

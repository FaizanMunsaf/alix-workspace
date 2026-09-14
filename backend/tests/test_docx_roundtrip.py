from core.parsers import parse_docx
from core.utils.export import ast_to_html, html_to_docx, html_to_text
from tests.helpers.docx import build_msa_docx


def test_ast_to_html_keeps_headings_clauses_and_table():
    _, tree = parse_docx(build_msa_docx())
    markup = ast_to_html(tree)

    assert "<h1>Master Services Agreement</h1>" in markup
    assert "<h2>Article 1 Definitions</h2>" in markup
    assert "<strong>1.1</strong>" in markup
    assert "Confidential Information" in markup
    assert "<table>" in markup
    assert "<th>Service</th>" in markup
    assert "<td>5000</td>" in markup


def test_html_round_trip_export_parses_back_to_usable_contract():
    _, tree = parse_docx(build_msa_docx())
    exported = html_to_docx(ast_to_html(tree))
    raw_text, parsed = parse_docx(exported)

    assert "Master Services Agreement" in raw_text
    assert "Confidential Information" in raw_text
    assert "Limitation of Liability" in raw_text
    assert "England and Wales" in raw_text
    assert any(node.node_type == "table" for node in _walk(parsed))
    assert "1.1" in raw_text


def test_html_to_text_strips_tags():
    text = html_to_text("<h1>Title</h1><p>Hello <strong>world</strong></p>")
    assert "Title" in text
    assert "Hello world" in text


def _walk(nodes):
    for node in nodes:
        yield node
        yield from _walk(node.children)

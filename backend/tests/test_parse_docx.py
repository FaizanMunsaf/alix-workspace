from core.parsers import parse_docx

from tests.helpers.docx import build_label_contract_docx, build_msa_docx
from tests.helpers.tree import by_title, by_type, first_title, walk


def test_parse_complex_legal_document_structure():
    raw_text, tree = parse_docx(build_msa_docx())

    assert "Master Services Agreement" in raw_text
    assert "Confidential Information" in raw_text
    assert "Limitation of Liability" in raw_text

    agreement = first_title(tree, "Master Services Agreement")
    assert agreement.node_type == "section"
    article_titles = [child.title for child in agreement.children]
    assert article_titles == [
        "Article 1 Definitions",
        "Article 2 Fees",
        "Article 3 Limitation of Liability",
    ]
    assert all(child.node_type == "heading" for child in agreement.children)

    article_1 = first_title(tree, "Article 1 Definitions")
    assert [child.title for child in article_1.children] == ["1.1", "1.2"]
    assert article_1.children[0].node_type == "sub_clause"
    assert article_1.children[0].metadata["number"] == "1.1"
    assert "Confidential Information" in (article_1.children[0].content or "")

    services = first_title(tree, "1.2")
    assert [child.title for child in services.children] == ["(a)", "(b)"]
    assert services.children[0].node_type == "sub_clause"
    assert services.children[0].metadata["source"] == "letter"
    roman = first_title(tree, "(iv)")
    assert roman.metadata["source"] == "roman"
    assert roman in services.children[1].children
    assert "agreed in writing" in (roman.content or "")


def test_parse_complex_legal_document_table_and_questions():
    _, tree = parse_docx(build_msa_docx())

    tables = by_type(tree, "table")
    assert len(tables) == 1
    table = tables[0]
    assert table.metadata["rows"] == 3
    assert table.metadata["cols"] == 3
    assert table.metadata["headers"] == ["Service", "Fee", "Currency"]
    assert "Service: Support | Fee: 5000" in (table.content or "")

    assert [child.node_type for child in table.children] == [
        "table_header",
        "table_row",
        "table_row",
    ]
    support_row = first_title(table.children, "Support")
    assert "Fee: 5000" in (support_row.content or "")
    assert [cell.node_type for cell in support_row.children] == [
        "table_cell",
        "table_cell",
        "table_cell",
    ]
    assert [cell.content for cell in support_row.children] == ["Support", "5000", "USD"]

    question = first_title(tree, "Q1 What is the governing law?")
    assert question.node_type == "section"
    assert question.metadata["number"] == "Q1"
    assert any(
        "England and Wales" in (child.content or "") for child in question.children
    )

    notice = first_title(tree, "Notice")
    assert notice.metadata["source"] == "bold_label"
    assert "email and courier" in (notice.content or "")


def test_parse_label_based_legal_document_without_heading_styles():
    raw_text, tree = parse_docx(build_label_contract_docx())

    assert "Affiliate" in raw_text
    article = first_title(tree, "Article 1.")
    assert article.node_type == "section"
    assert article.content == "Definitions"
    assert article.metadata["source"] == "label"
    assert first_title(article.children, "1.1").content.startswith("Affiliate")

    section = first_title(tree, "Section 2")
    assert section.content == "Term"
    clause = first_title(section.children, "2.1")
    assert clause.node_type == "sub_clause"
    assert [child.title for child in clause.children] == ["(a)"]
    roman = first_title(clause.children, "(ii)")
    assert roman.metadata["source"] == "roman"


def test_parse_docx_preserves_document_order_in_raw_text():
    raw_text, tree = parse_docx(build_msa_docx())

    assert raw_text.index("Article 1") < raw_text.index("Article 2")
    assert raw_text.index("Article 2") < raw_text.index("Article 3")
    assert raw_text.index("1.1") < raw_text.index("3.1")
    assert len(list(walk(tree))) >= 20


def test_parse_empty_paragraphs_are_ignored():
    from tests.helpers.docx import build_docx

    _, tree = parse_docx(
        build_docx([("p", "1.1 Keep this clause."), ("p", "   "), ("p", "")])
    )

    assert [node.title for node in by_title(tree, "1.1")] == ["1.1"]
    assert by_type(tree, "paragraph") == []

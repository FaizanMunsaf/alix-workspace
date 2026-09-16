from core.ast.diff import diff_ast
from core.ast.parsers import ASTNode, parse_docx

from tests.helpers.docx import build_msa_docx


# this function use for build a clause node in tests
def _clause(
    number: str, content: str, children: list[ASTNode] | None = None
) -> ASTNode:
    return ASTNode(
        node_type="clause",
        level=10,
        title=number,
        content=content,
        metadata={"source": "number", "number": number},
        children=children or [],
    )


# this function use for build a sub-clause node in tests
def _sub(mark: str, content: str, source: str = "letter") -> ASTNode:
    return ASTNode(
        node_type="sub_clause",
        level=20,
        title=f"({mark})",
        content=content,
        metadata={"source": source, "number": mark},
    )


# this function use for build a section node in tests
def _section(title: str, children: list[ASTNode]) -> ASTNode:
    return ASTNode(node_type="section", level=1, title=title, children=children)


# this function use for check same trees have no diff
def test_diff_identical_trees_is_empty():
    tree = [_section("Article 1", [_clause("1.1", "Same text.")])]
    result = diff_ast(tree, tree)

    assert result.added == []
    assert result.deleted == []
    assert result.modified == []
    assert result.to_dict()["summary"] == {"added": 0, "deleted": 0, "modified": 0}


# this function use for check added, deleted and modified clauses
def test_diff_detects_added_deleted_and_modified_clauses():
    old = [
        _section(
            "Article 1",
            [
                _clause("1.1", "Old definition of confidential information."),
                _clause(
                    "1.2",
                    "Services means professional services.",
                    [_sub("a", "implementation"), _sub("b", "support")],
                ),
            ],
        )
    ]
    new = [
        _section(
            "Article 1",
            [
                _clause("1.1", "Expanded definition of confidential information."),
                _clause(
                    "1.2",
                    "Services means professional services.",
                    [_sub("a", "implementation"), _sub("c", "training")],
                ),
                _clause("1.3", "Deliverables are defined in Exhibit B."),
            ],
        )
    ]

    result = diff_ast(old, new)
    added_titles = {change.title for change in result.added}
    deleted_titles = {change.title for change in result.deleted}
    modified = {change.title: change for change in result.modified}

    assert added_titles == {"1.3", "(c)"}
    assert deleted_titles == {"(b)"}
    assert "1.1" in modified
    assert modified["1.1"].fields == ["content"]
    assert "Old definition" in (modified["1.1"].before or {}).get("content", "")
    assert "Expanded definition" in (modified["1.1"].after or {}).get("content", "")
    assert result.to_dict()["summary"] == {"added": 2, "deleted": 1, "modified": 1}


# this function use for check similar paragraphs count as modified
def test_diff_treats_similar_unnumbered_paragraphs_as_modified():
    old = [
        ASTNode(
            node_type="paragraph",
            level=50,
            content="The governing law is England.",
        )
    ]
    new = [
        ASTNode(
            node_type="paragraph",
            level=50,
            content="The governing law is England and Wales.",
        )
    ]

    result = diff_ast(old, new)

    assert result.added == []
    assert result.deleted == []
    assert len(result.modified) == 1
    assert result.modified[0].fields == ["content"]


# this function use for check diff works with saved ast_json
def test_diff_accepts_persisted_ast_json_payload():
    old = {"nodes": [_clause("3.1", "No consequential damages.").to_dict()]}
    new = {"nodes": [_clause("3.1", "No indirect or consequential damages.").to_dict()]}

    result = diff_ast(old, new)

    assert [change.title for change in result.modified] == ["3.1"]
    assert result.added == []
    assert result.deleted == []


# this function use for check diff on two parsed legal document versions
def test_diff_parsed_legal_document_versions():
    _, old_tree = parse_docx(build_msa_docx())
    _, new_tree = parse_docx(
        build_msa_docx(
            confidential_text=(
                "Confidential Information means non-public business, technical, "
                "and financial information disclosed by a party."
            ),
            include_support_subclause=False,
            include_training_subclause=True,
            include_payment_clause=True,
            include_indemnity=True,
            support_fee="6000",
        )
    )

    result = diff_ast(old_tree, new_tree)
    added_titles = {change.title for change in result.added}
    deleted_titles = {change.title for change in result.deleted}
    modified_titles = {change.title for change in result.modified}

    assert "1.1" in modified_titles
    assert "(b)" in deleted_titles
    assert "(c)" in added_titles
    assert "2.2" in added_titles
    assert "Article 4 Indemnity" in added_titles
    assert "4.1" in added_titles
    assert "Support" in modified_titles
    assert any(
        change.title == "Support" and "content" in change.fields
        for change in result.modified
    )
    assert any(
        "6000" in (change.after or {}).get("content", "") for change in result.modified
    )

    old_json = {"nodes": [node.to_dict() for node in old_tree]}
    new_json = {"nodes": [node.to_dict() for node in new_tree]}
    from_json = diff_ast(old_json, new_json)
    assert from_json.to_dict()["summary"] == result.to_dict()["summary"]

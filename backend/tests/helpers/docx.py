from io import BytesIO

from docx import Document
from docx.table import Table


def build_docx(blocks: list) -> bytes:
    document = Document()
    for block in blocks:
        kind = block[0]
        if kind == "heading":
            document.add_heading(block[2], level=block[1])
        elif kind == "p":
            document.add_paragraph(block[1])
        elif kind == "bold":
            paragraph = document.add_paragraph()
            run = paragraph.add_run(block[1])
            run.bold = True
        elif kind == "label":
            paragraph = document.add_paragraph()
            label = paragraph.add_run(block[1])
            label.bold = True
            paragraph.add_run(block[2])
        elif kind == "table":
            _add_table(document, headers=block[1], rows=block[2])
        else:
            raise ValueError(f"Unknown block type: {kind}")
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def build_msa_docx(
    *,
    confidential_text: str = (
        "Confidential Information means all non-public information disclosed by a party."
    ),
    include_support_subclause: bool = True,
    include_training_subclause: bool = False,
    include_payment_clause: bool = False,
    include_indemnity: bool = False,
    support_fee: str = "5000",
) -> bytes:
    blocks: list = [
        ("heading", 1, "Master Services Agreement"),
        ("heading", 2, "Article 1 Definitions"),
        ("p", f"1.1 {confidential_text}"),
        ("p", "1.2 Services means the professional services described in Exhibit A."),
        ("p", "(a) implementation of the platform"),
    ]
    if include_support_subclause:
        blocks.append(("p", "(b) ongoing support and maintenance"))
    if include_training_subclause:
        blocks.append(("p", "(c) end-user training"))
    blocks.extend(
        [
            ("p", "(iv) any other services agreed in writing"),
            ("heading", 2, "Article 2 Fees"),
            ("p", "2.1 Fees are set out in the table below."),
            (
                "table",
                ["Service", "Fee", "Currency"],
                [
                    ["Implementation", "25000", "USD"],
                    ["Support", support_fee, "USD"],
                ],
            ),
        ]
    )
    if include_payment_clause:
        blocks.append(("p", "2.2 Payment is due within thirty (30) days of invoice."))
    blocks.extend(
        [
            ("heading", 2, "Article 3 Limitation of Liability"),
            ("p", "3.1 Neither party shall be liable for consequential damages."),
            ("p", "(a) the liability cap equals fees paid in the prior twelve months"),
        ]
    )
    if include_indemnity:
        blocks.extend(
            [
                ("heading", 2, "Article 4 Indemnity"),
                (
                    "p",
                    "4.1 Each party shall indemnify the other against third-party claims.",
                ),
            ]
        )
    blocks.extend(
        [
            ("bold", "Q1. What is the governing law?"),
            ("p", "The laws of England and Wales."),
            ("label", "Notice: ", "notices must be sent by email and courier."),
        ]
    )
    return build_docx(blocks)


def build_label_contract_docx() -> bytes:
    return build_docx(
        [
            ("p", "Article 1. Definitions"),
            ("p", "1.1 Affiliate means any entity that controls a party."),
            ("p", "Section 2 Term"),
            ("p", "2.1 This Agreement commences on the Effective Date."),
            ("p", "(a) the initial term is twelve months"),
            ("p", "(ii) renewal is automatic unless notice is given"),
        ]
    )


def _add_table(document: Document, headers: list[str], rows: list[list[str]]) -> Table:
    table = document.add_table(rows=1 + len(rows), cols=len(headers))
    for index, header in enumerate(headers):
        table.rows[0].cells[index].text = header
    for row_index, values in enumerate(rows, start=1):
        for col_index, value in enumerate(values):
            table.rows[row_index].cells[col_index].text = value
    return table

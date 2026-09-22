import uuid
from io import BytesIO
from pathlib import Path

from docx import Document
from docx.shared import Inches

from core.ast.parsers import parse_docx
from core.ast.parsers.helpers.extract_images import (
    iter_paragraph_images,
    media_url,
    resolve_image_bytes,
)
from core.utils.export import ast_to_html, html_to_docx
from core.utils.export.node_to_html import node_to_html


def _tiny_png() -> bytes:
    import base64

    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )


def _docx_with_image() -> bytes:
    document = Document()
    document.add_paragraph("Before image")
    document.add_picture(BytesIO(_tiny_png()), width=Inches(1))
    document.add_paragraph("After image")
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_parse_docx_stores_images_on_disk(tmp_path: Path):
    document_id = str(uuid.uuid4())
    media_dir = tmp_path / "media"
    raw_text, tree = parse_docx(
        _docx_with_image(),
        document_id=document_id,
        media_dir=media_dir,
    )
    assert "Before image" in raw_text
    assert "After image" in raw_text
    images = [node for node in tree if node.node_type == "image"]
    assert len(images) == 1
    src = images[0].metadata["src"]
    assert src.startswith(f"/api/v1/documents/{document_id}/media/")
    filename = images[0].metadata["filename"]
    assert (media_dir / filename).is_file()
    assert not src.startswith("data:")


def test_ast_to_html_renders_media_url(tmp_path: Path):
    document_id = str(uuid.uuid4())
    _, tree = parse_docx(
        _docx_with_image(),
        document_id=document_id,
        media_dir=tmp_path / "media",
    )
    markup = ast_to_html(tree)
    assert "<img" in markup
    assert f"/api/v1/documents/{document_id}/media/" in markup
    assert "data:image/" not in markup


def test_html_to_docx_roundtrips_media_url(tmp_path: Path):
    document_id = str(uuid.uuid4())
    media_dir = tmp_path / document_id / "media"
    media_dir.mkdir(parents=True)
    filename = "pic.png"
    (media_dir / filename).write_bytes(_tiny_png())
    src = media_url(document_id, filename)
    markup = f'<p>Intro</p><p><img src="{src}" alt=""></p><p>Outro</p>'
    data = html_to_docx(markup, uploads_dir=tmp_path)
    document = Document(BytesIO(data))
    texts = [p.text.strip() for p in document.paragraphs if p.text.strip()]
    assert "Intro" in texts
    assert "Outro" in texts
    images = []
    for paragraph in document.paragraphs:
        images.extend(iter_paragraph_images(paragraph, document))
    assert len(images) >= 1


def test_resolve_image_bytes_reads_media_file(tmp_path: Path):
    document_id = str(uuid.uuid4())
    media_dir = tmp_path / document_id / "media"
    media_dir.mkdir(parents=True)
    filename = "a.png"
    (media_dir / filename).write_bytes(_tiny_png())
    blob = resolve_image_bytes(media_url(document_id, filename), uploads_dir=tmp_path)
    assert blob == _tiny_png()


def test_node_to_html_skips_image_without_src():
    from core.ast.parsers.ast import ASTNode

    html = node_to_html(ASTNode(node_type="image", level=50, metadata={}))
    assert html == ""

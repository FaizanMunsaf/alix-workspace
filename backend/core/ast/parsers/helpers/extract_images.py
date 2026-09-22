import mimetypes
import re
import uuid
from pathlib import Path

from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

_CONTENT_TYPE_EXT = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/bmp": ".bmp",
}
_SAFE_MEDIA_NAME = re.compile(r"^[A-Za-z0-9._-]+$")
_MEDIA_URL = re.compile(
    r"^/api/v1/documents/(?P<document_id>[0-9a-fA-F-]{36})/media/(?P<filename>[A-Za-z0-9._-]+)$"
)


def iter_paragraph_images(paragraph: Paragraph, document) -> list[tuple[str, bytes]]:
    """Return (content_type, blob) for inline images in a paragraph."""
    images: list[tuple[str, bytes]] = []
    for blip in paragraph._element.findall(".//" + qn("a:blip")):
        embed = blip.get(qn("r:embed"))
        if not embed:
            continue
        try:
            part = document.part.related_parts[embed]
        except KeyError:
            continue
        content_type = getattr(part, "content_type", None) or "image/png"
        blob = getattr(part, "blob", None)
        if not blob:
            continue
        images.append((content_type, blob))
    return images


def media_url(document_id: str, filename: str) -> str:
    return f"/api/v1/documents/{document_id}/media/{filename}"


def extension_for_content_type(content_type: str) -> str:
    return _CONTENT_TYPE_EXT.get(content_type.lower(), ".bin")


def store_document_image(
    *,
    document_id: str,
    media_dir: Path,
    content_type: str,
    blob: bytes,
) -> dict:
    """Write image bytes to disk and return metadata with a URL src."""
    media_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{extension_for_content_type(content_type)}"
    path = media_dir / filename
    path.write_bytes(blob)
    return {
        "src": media_url(document_id, filename),
        "content_type": content_type,
        "filename": filename,
    }


def resolve_image_bytes(src: str, *, uploads_dir: Path) -> bytes | None:
    """Load image bytes from a media URL or legacy data URI."""
    if not src:
        return None
    if src.startswith("data:"):
        return _decode_data_uri(src)

    match = _MEDIA_URL.match(src.strip())
    if match is None:
        return None
    document_id = match.group("document_id")
    filename = match.group("filename")
    if not _SAFE_MEDIA_NAME.match(filename):
        return None
    path = (uploads_dir / document_id / "media" / filename).resolve()
    media_root = (uploads_dir / document_id / "media").resolve()
    try:
        path.relative_to(media_root)
    except ValueError:
        return None
    if not path.is_file():
        return None
    return path.read_bytes()


def media_file_path(
    *, uploads_dir: Path, document_id: str, filename: str
) -> Path | None:
    if not _SAFE_MEDIA_NAME.match(filename):
        return None
    path = (uploads_dir / document_id / "media" / filename).resolve()
    media_root = (uploads_dir / document_id / "media").resolve()
    try:
        path.relative_to(media_root)
    except ValueError:
        return None
    return path


def guess_content_type(filename: str) -> str:
    guessed, _ = mimetypes.guess_type(filename)
    return guessed or "application/octet-stream"


def _decode_data_uri(src: str) -> bytes | None:
    import base64
    import binascii

    try:
        header, payload = src.split(",", 1)
    except ValueError:
        return None
    if ";base64" not in header:
        return None
    try:
        return base64.b64decode(payload)
    except (ValueError, TypeError, binascii.Error):
        return None

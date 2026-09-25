import re
from html import unescape


class PatchConflict(ValueError):
    pass


_WS_RE = re.compile(r"\s+")
_TOKEN_RE = re.compile(r"(<[^>]+>|&[a-zA-Z0-9#]+;|[^<&]+)")
_EMPTY_INLINE_RE = re.compile(
    r"<(strong|em|b|i|u)(?:\s[^>]*)?>\s*</\1>",
    flags=re.IGNORECASE,
)


def apply_text_patch(html: str, before: str, after: str, *, occurrence: int = 0) -> str:
    target = (before or "").strip()
    if not target:
        raise PatchConflict("The original text is empty.")
    if occurrence < 0:
        raise PatchConflict("occurrence must be >= 0.")

    # Fast path: contiguous exact match in the HTML markup.
    if target in html:
        start = 0
        for _ in range(occurrence + 1):
            hit = html.find(target, start)
            if hit == -1:
                raise PatchConflict("The original text is no longer in the document.")
            start = hit + 1
        hit = start - 1
        return html[:hit] + after + html[hit + len(target) :]

    updated = _apply_across_markup(html, target, after, occurrence=occurrence)
    if updated is None:
        raise PatchConflict("The original text is no longer in the document.")
    return _EMPTY_INLINE_RE.sub("", updated)


def plain_text_in_html(html: str, needle: str) -> bool:
    return count_plain_matches(html, needle) > 0


def count_plain_matches(html: str, needle: str) -> int:
    target = (needle or "").strip()
    if not target:
        return 0
    if target in html:
        count = 0
        start = 0
        while True:
            hit = html.find(target, start)
            if hit == -1:
                break
            count += 1
            start = hit + max(1, len(target))
        return count
    return len(_plain_ranges(html, target))


def uniquify_excerpt(html: str, excerpt: str, context: str) -> str | None:
    """Expand ``excerpt`` inside ``context`` until it appears once in ``html``.

    Returns None when the excerpt cannot be found. If it cannot be made unique,
    returns the longest available expansion (caller may still use occurrence).
    """
    target = (excerpt or "").strip()
    if not target:
        return None
    if not plain_text_in_html(html, target):
        return None
    if count_plain_matches(html, target) == 1:
        return target

    haystack = context or ""
    idx = haystack.find(target)
    if idx == -1:
        # Try whitespace-normalized locate inside context.
        collapsed_context, map_back = _collapse_map(haystack)
        collapsed_target = _normalize_ws(target)
        hit = collapsed_context.find(collapsed_target)
        if hit == -1 or not map_back:
            return target
        start = map_back[hit]
        end = map_back[hit + len(collapsed_target) - 1] + 1
    else:
        start = idx
        end = idx + len(target)

    left = start
    right = end
    candidate = haystack[left:right].strip()
    while count_plain_matches(html, candidate) > 1 and (
        left > 0 or right < len(haystack)
    ):
        if left > 0:
            left -= 1
        if (
            right < len(haystack)
            and count_plain_matches(html, haystack[left:right].strip()) > 1
        ):
            right += 1
        candidate = haystack[left:right].strip()
        if not candidate:
            break
    return candidate or target


def _apply_across_markup(
    html: str, target: str, after: str, *, occurrence: int = 0
) -> str | None:
    ranges = _plain_ranges(html, target)
    if occurrence >= len(ranges):
        return None
    start_plain, end_plain = ranges[occurrence]
    tokens = _tokenize(html)

    out: list[str] = []
    plain_index = 0
    emitted_replacement = False
    for kind, value in tokens:
        if kind == "tag":
            out.append(value)
            continue

        text = unescape(value) if kind == "entity" else value
        text_start = plain_index
        text_end = plain_index + len(text)
        plain_index = text_end

        if text_end <= start_plain or text_start >= end_plain:
            out.append(value if kind == "entity" else text)
            continue

        keep_prefix = max(0, start_plain - text_start)
        keep_suffix = max(0, text_end - end_plain)
        if keep_prefix:
            out.append(text[:keep_prefix])
        if not emitted_replacement:
            out.append(after)
            emitted_replacement = True
        if keep_suffix:
            out.append(text[len(text) - keep_suffix :])
    return "".join(out)


def _plain_ranges(html: str, needle: str) -> list[tuple[int, int]]:
    tokens = _tokenize(html)
    plain_parts: list[str] = []
    for kind, value in tokens:
        if kind == "tag":
            continue
        plain_parts.append(unescape(value) if kind == "entity" else value)
    plain = "".join(plain_parts)
    target = needle.strip()
    ranges: list[tuple[int, int]] = []

    start = 0
    while True:
        hit = plain.find(target, start)
        if hit == -1:
            break
        ranges.append((hit, hit + len(target)))
        start = hit + max(1, len(target))

    if ranges:
        return ranges

    collapsed, map_back = _collapse_map(plain)
    collapsed_target = _normalize_ws(needle)
    if not collapsed_target or not map_back:
        return []
    start = 0
    while True:
        hit = collapsed.find(collapsed_target, start)
        if hit == -1:
            break
        plain_start = map_back[hit]
        plain_end = map_back[hit + len(collapsed_target) - 1] + 1
        ranges.append((plain_start, plain_end))
        start = hit + max(1, len(collapsed_target))
    return ranges


def _tokenize(html: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    for match in _TOKEN_RE.finditer(html or ""):
        piece = match.group(0)
        if piece.startswith("<"):
            tokens.append(("tag", piece))
        elif piece.startswith("&"):
            tokens.append(("entity", piece))
        else:
            tokens.append(("text", piece))
    return tokens


def _collapse_map(plain: str) -> tuple[str, list[int]]:
    collapsed: list[str] = []
    map_back: list[int] = []
    prev_space = False
    for index, char in enumerate(plain):
        if char.isspace():
            if prev_space or not collapsed:
                continue
            collapsed.append(" ")
            map_back.append(index)
            prev_space = True
            continue
        collapsed.append(char)
        map_back.append(index)
        prev_space = False
    return "".join(collapsed).strip(), map_back


def _normalize_ws(text: str) -> str:
    return _WS_RE.sub(" ", text).strip()

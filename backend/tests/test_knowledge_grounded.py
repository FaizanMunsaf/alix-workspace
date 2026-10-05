from seeds.knowledge_seed import chunk_markdown, knowledge_dir
from ds.intelligences.layered_retrieve import LayeredHit, format_layer_blocks
from ds.rag.prompts import load_prompt


def test_knowledge_seed_files_exist():
    directory = knowledge_dir()
    assert (directory / "playbook_liability.md").is_file()
    assert (directory / "playbook_confidentiality.md").is_file()
    assert (directory / "public_ucta_summary.md").is_file()


def test_chunk_markdown_splits_long_text():
    text = "\n\n".join(f"Block {index} " + ("word " * 40) for index in range(6))
    parts = chunk_markdown(text, max_chars=200)
    assert len(parts) > 1
    assert all(part.strip() for part in parts)


def test_format_layer_blocks_labels_layers():
    hits = [
        LayeredHit(
            "contract", "Contract 1", "paragraph", "Liability is uncapped.", 0.1
        ),
        LayeredHit(
            "playbook",
            "Playbook 1",
            "Negotiation playbook — Liability",
            "Cap at 12 months of fees.",
            0.2,
        ),
        LayeredHit(
            "public_ref",
            "Public 1",
            "UCTA stub",
            "Carve out death and personal injury.",
            0.3,
        ),
    ]
    contract = format_layer_blocks(hits, "contract")
    playbook = format_layer_blocks(hits, "playbook")
    public = format_layer_blocks(hits, "public_ref")
    assert contract.startswith("[Contract 1]")
    assert "uncapped" in contract
    assert playbook.startswith("[Playbook 1]")
    assert "12 months" in playbook
    assert public.startswith("[Public 1]")
    assert format_layer_blocks(hits, "missing") == "(none)"


def test_grounded_review_prompt_distinguishes_layers():
    text = load_prompt("grounded_review")
    assert "{contract}" in text
    assert "{playbook}" in text
    assert "{public}" in text
    assert "Playbook" in text
    assert "Public" in text

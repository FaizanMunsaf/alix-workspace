import pytest

from ds.rag.prompts import load_prompt


def test_load_prompt_reads_file_by_name():
    text = load_prompt("edit_selection")
    assert "{instruction}" in text
    assert "{selection}" in text


def test_load_prompt_missing_name_raises():
    with pytest.raises(FileNotFoundError):
        load_prompt("does_not_exist")

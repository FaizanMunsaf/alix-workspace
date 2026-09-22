import pytest

from ds.rag.prompts import load_prompt


def test_load_prompt_reads_file_by_name():
    text = load_prompt("edit_selection")
    assert "{instruction}" in text
    assert "{selection}" in text


def test_load_prompt_qa_includes_selection():
    text = load_prompt("qa")
    assert "{selection}" in text
    assert "{context}" in text
    assert "{query}" in text


def test_load_prompt_missing_name_raises():
    with pytest.raises(FileNotFoundError):
        load_prompt("does_not_exist")

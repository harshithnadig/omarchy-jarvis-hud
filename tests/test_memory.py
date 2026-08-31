import pytest
from core.memory.dictionary import PersonalDictionary
from core.memory.snippets import SnippetManager

def test_personal_dictionary_builtins(tmp_path):
    db_file = str(tmp_path / "dict.db")
    dictionary = PersonalDictionary(db_path=db_file)

    # Builtin replacements
    text = "we are testing on hyper land with fast api"
    polished = dictionary.apply_dictionary(text)
    assert "Hyprland" in polished
    assert "FastAPI" in polished

def test_personal_dictionary_custom_entry(tmp_path):
    db_file = str(tmp_path / "dict.db")
    dictionary = PersonalDictionary(db_path=db_file)

    dictionary.add_entry("harshu", "Harshith Nadig", app_scope="global")
    text = "hello harshu welcome back"
    assert dictionary.apply_dictionary(text) == "hello Harshith Nadig welcome back"

def test_snippet_expansion(tmp_path):
    snip_file = str(tmp_path / "snippets.json")
    mgr = SnippetManager(snippets_path=snip_file)

    mgr.add_snippet("insert my email", "developer@omarchy.org")
    assert mgr.expand_snippets("insert my email") == "developer@omarchy.org"
    assert mgr.expand_snippets("just regular speech") == "just regular speech"

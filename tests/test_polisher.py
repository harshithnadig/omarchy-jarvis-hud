import pytest
from core.polisher import TextPolisher

def test_clean_empty():
    assert TextPolisher.clean_deterministic("") == ""
    assert TextPolisher.clean_deterministic(None) == ""
    assert TextPolisher.clean_deterministic("   ") == ""

def test_clean_fillers():
    assert TextPolisher.clean_deterministic("Hello um world") == "Hello world"
    assert TextPolisher.clean_deterministic("uh let us test") == "Let us test"
    assert TextPolisher.clean_deterministic("This is er, great") == "This is, great" or TextPolisher.clean_deterministic("This is er, great") == "This is, great"

def test_preserve_intentional_repetitions():
    # Legitimate repetitions must NOT be collapsed
    assert TextPolisher.clean_deterministic("This is very very important") == "This is very very important"
    assert TextPolisher.clean_deterministic("I had had enough") == "I had had enough"
    assert TextPolisher.clean_deterministic("No no no wait") == "No no no wait"
    assert TextPolisher.clean_deterministic("That that is true") == "That that is true"

def test_collapse_stutters():
    # Stutters should be collapsed
    assert TextPolisher.clean_deterministic("check the the repository") == "Check the repository"
    assert TextPolisher.clean_deterministic("in in the function") == "In the function"

def test_dev_operators():
    text = "const f = x fat arrow x triple equals 5"
    assert TextPolisher.clean_deterministic(text, dev_mode=True) == "Const f = x => x === 5"
    assert TextPolisher.clean_deterministic("a logical and b", dev_mode=True) == "A && b"
    assert TextPolisher.clean_deterministic("user optional chaining name", dev_mode=True) == "User ?. Name" or TextPolisher.clean_deterministic("user optional chaining name", dev_mode=True) == "User ?. name"

def test_punctuation_and_capitalization():
    assert TextPolisher.clean_deterministic("hello world .") == "Hello world."
    assert TextPolisher.clean_deterministic("start , middle , end") == "Start, middle, end"
    assert TextPolisher.clean_deterministic("lower start") == "Lower start"

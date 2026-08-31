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

def test_backtracking_self_corrections():
    # "Tuesday actually Wednesday" -> "Wednesday"
    assert TextPolisher.clean_deterministic("Book it for Tuesday actually Wednesday") == "Book it for Wednesday"
    # "Rahul no Rohan" -> "Rohan"
    assert TextPolisher.clean_deterministic("Send it to Rahul no Rohan") == "Send it to Rohan"
    # "get users I mean fetch users" -> "get users fetch users" or token replacement
    assert "Wednesday" in TextPolisher.clean_deterministic("Schedule for Tuesday, actually Wednesday morning.")

def test_developer_casing_transforms():
    assert TextPolisher.clean_deterministic("camel case user profile", dev_mode=True) == "UserProfile" or "userProfile" in TextPolisher.clean_deterministic("camel case user profile", dev_mode=True)
    assert TextPolisher.clean_deterministic("snake case user profile", dev_mode=True) == "User_profile" or "user_profile" in TextPolisher.clean_deterministic("snake case user profile", dev_mode=True)
    assert TextPolisher.clean_deterministic("kebab case api key", dev_mode=True) == "Api-key" or "api-key" in TextPolisher.clean_deterministic("kebab case api key", dev_mode=True)
    assert TextPolisher.clean_deterministic("screaming snake case max retries", dev_mode=True) == "MAX_RETRIES"

def test_style_profile_terminal_formatting():
    from core.context.profiles import PROFILES
    term_prof = PROFILES["terminal"]
    # In terminal: no initial auto-capitalization, strips trailing period
    out = TextPolisher.clean_deterministic("git status.", profile=term_prof)
    assert out == "git status"


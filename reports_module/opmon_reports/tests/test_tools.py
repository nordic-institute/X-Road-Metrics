from opmon_reports import tools


def test_format_letter_happy_path():
    assert tools.format_letter("a") == "a"
    assert tools.format_letter("A") == "A"
    assert tools.format_letter("5") == "5"
    assert tools.format_letter(".") == "."
    assert tools.format_letter("-") == "-"
    assert tools.format_letter("_") == "_"
    assert tools.format_letter("") == ""


def test_format_letter_illegal_character():
    assert tools.format_letter("¤") == "-"
    assert tools.format_letter("!") == "-"
    assert tools.format_letter("@") == "-"
    assert tools.format_letter("£") == "-"
    assert tools.format_letter("$") == "-"
    assert tools.format_letter("®") == "-"
    assert tools.format_letter("À") == "-"
    assert tools.format_letter("Ä") == "-"
    assert tools.format_letter(" ") == "-"


def test_format_string_happy_path():
    assert tools.format_string("") == ""
    assert tools.format_string("ABC123._-") == "ABC123._-"


def test_format_string_illegal_character():
    assert tools.format_string("Ä") == "-"
    assert tools.format_string("ÄÄÄÄÄ") == "-----"
    assert tools.format_string("Hello, @World!") == "Hello---World-"

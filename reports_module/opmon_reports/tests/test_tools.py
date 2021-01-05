import unittest

from ..reportslib import tools


# To run the tests:
# python -m reports_module.tests.test_tools


class TestTools(unittest.TestCase):
    def test_format_letter_happy_path(self):
        self.assertEqual(tools.format_letter("a"), "a")
        self.assertEqual(tools.format_letter("A"), "A")
        self.assertEqual(tools.format_letter("5"), "5")
        self.assertEqual(tools.format_letter("."), ".")
        self.assertEqual(tools.format_letter("-"), "-")
        self.assertEqual(tools.format_letter("_"), "_")
        self.assertEqual(tools.format_letter(""), "")

    def test_format_letter_illegal_character(self):
        self.assertEqual(tools.format_letter("¤"), "-")
        self.assertEqual(tools.format_letter("!"), "-")
        self.assertEqual(tools.format_letter("@"), "-")
        self.assertEqual(tools.format_letter("£"), "-")
        self.assertEqual(tools.format_letter("$"), "-")
        self.assertEqual(tools.format_letter("®"), "-")
        self.assertEqual(tools.format_letter("À"), "-")
        self.assertEqual(tools.format_letter("Ä"), "-")
        self.assertEqual(tools.format_letter(" "), "-")

    def test_format_string_happy_path(self):
        self.assertEqual(tools.format_string(""), "")
        self.assertEqual(tools.format_string("ABC123._-"), "ABC123._-")

    def test_format_string_illegal_character(self):
        self.assertEqual(tools.format_string("Ä"), "-")
        self.assertEqual(tools.format_string("ÄÄÄÄÄ"), "-----")
        self.assertEqual(tools.format_string("Hello, @World!"), "Hello---World-")


if __name__ == '__main__':
    unittest.main()

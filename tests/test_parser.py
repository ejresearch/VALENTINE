"""Tests for the screenplay parser module."""

import pytest
from screenplay_formatter.parser import ScreenplayParser, ElementType, ScreenplayElement


class TestScreenplayParser:
    """Test screenplay parser functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ScreenplayParser()

    def test_parse_scene_heading(self):
        """Test parsing of scene headings."""
        text = "INT. COFFEE SHOP - DAY"
        elements = self.parser.parse(text)

        assert len(elements) == 1
        assert elements[0].type == ElementType.SCENE_HEADING
        assert elements[0].content == "INT. COFFEE SHOP - DAY"

    def test_parse_scene_heading_variations(self):
        """Test various scene heading formats."""
        variations = [
            "EXT. PARK - NIGHT",
            "INT./EXT. CAR - CONTINUOUS",
            "I/E. DOORWAY - DAWN",
            "INT. OFFICE - LATER",
            "EXT. STREET - MOMENTS LATER"
        ]

        for heading in variations:
            elements = self.parser.parse(heading)
            assert elements[0].type == ElementType.SCENE_HEADING

    def test_parse_character_name(self):
        """Test parsing of character names."""
        text = """JOHN DOE
Hello, world!"""
        elements = self.parser.parse(text)

        assert elements[0].type == ElementType.CHARACTER
        assert elements[0].content == "JOHN DOE"
        assert elements[1].type == ElementType.DIALOGUE

    def test_parse_character_with_extension(self):
        """Test character names with extensions."""
        extensions = ["(V.O.)", "(O.S.)", "(CONT'D)", "(O.C.)"]

        for ext in extensions:
            text = f"CHARACTER {ext}\nDialogue here"
            elements = self.parser.parse(text)
            assert elements[0].type == ElementType.CHARACTER

    def test_parse_dialogue(self):
        """Test parsing of dialogue."""
        text = """SARAH
This is my dialogue.
It can span multiple lines."""

        elements = self.parser.parse(text)
        assert elements[0].type == ElementType.CHARACTER
        assert elements[1].type == ElementType.DIALOGUE
        assert elements[2].type == ElementType.DIALOGUE

    def test_parse_parenthetical(self):
        """Test parsing of parentheticals."""
        text = """CHARACTER
(whispering)
This is spoken quietly."""

        elements = self.parser.parse(text)
        assert elements[0].type == ElementType.CHARACTER
        assert elements[1].type == ElementType.PARENTHETICAL
        assert elements[1].content == "(whispering)"
        assert elements[2].type == ElementType.DIALOGUE

    def test_parse_action(self):
        """Test parsing of action lines."""
        text = "The door opens slowly. A figure enters the room."
        elements = self.parser.parse(text)

        assert elements[0].type == ElementType.ACTION

    def test_parse_transition(self):
        """Test parsing of transitions."""
        transitions = [
            "FADE IN:",
            "FADE OUT.",
            "CUT TO:",
            "DISSOLVE TO:",
            "MATCH CUT TO:",
            "THE END"
        ]

        for transition in transitions:
            elements = self.parser.parse(transition)
            assert elements[0].type == ElementType.TRANSITION

    def test_parse_montage(self):
        """Test parsing of montage markers."""
        text = """BEGIN MONTAGE
-- Scene 1
-- Scene 2
END MONTAGE"""

        elements = self.parser.parse(text)
        assert elements[0].type == ElementType.MONTAGE_BEGIN
        assert elements[-1].type == ElementType.MONTAGE_END

    def test_parse_title(self):
        """Test parsing of titles and chyrons."""
        # Note: TITLE: at start can be ambiguous (title page vs on-screen title)
        # Use other patterns or provide context (e.g., after a scene heading)
        titles = [
            "CHYRON: Three Years Later",
            "SUPER: London, 1942"
        ]

        for title in titles:
            elements = self.parser.parse(title)
            assert elements[0].type == ElementType.TITLE

        # Test TITLE: with screenplay context (after scene heading)
        text = """INT. OFFICE - DAY

TITLE: Chapter One"""
        elements = self.parser.parse(text)
        title_elem = [e for e in elements if e.type == ElementType.TITLE]
        assert len(title_elem) == 1

    def test_parse_complete_scene(self):
        """Test parsing a complete scene."""
        text = """INT. OFFICE - DAY

John sits at his desk.

JOHN
(frustrated)
This isn't working!

He stands and walks to the window.

CUT TO:"""

        elements = self.parser.parse(text)

        assert elements[0].type == ElementType.SCENE_HEADING
        assert elements[1].type == ElementType.BLANK
        assert elements[2].type == ElementType.ACTION
        assert elements[3].type == ElementType.BLANK
        assert elements[4].type == ElementType.CHARACTER
        assert elements[5].type == ElementType.PARENTHETICAL
        assert elements[6].type == ElementType.DIALOGUE
        assert elements[7].type == ElementType.BLANK
        assert elements[8].type == ElementType.ACTION
        assert elements[9].type == ElementType.BLANK
        assert elements[10].type == ElementType.TRANSITION

    def test_parse_dialogue_block_context(self):
        """Test that dialogue context is properly maintained."""
        text = """SARAH
First line of dialogue.

Still in the dialogue block.

JOHN
Different character now."""

        elements = self.parser.parse(text)

        assert elements[0].type == ElementType.CHARACTER
        assert elements[1].type == ElementType.DIALOGUE
        assert elements[2].type == ElementType.BLANK
        assert elements[3].type == ElementType.ACTION  # Not dialogue anymore
        assert elements[4].type == ElementType.BLANK
        assert elements[5].type == ElementType.CHARACTER

    def test_parse_empty_text(self):
        """Test parsing empty text."""
        elements = self.parser.parse("")
        assert len(elements) == 0

    def test_parse_only_blank_lines(self):
        """Test parsing text with only blank lines."""
        text = "\n\n\n"
        elements = self.parser.parse(text)

        assert all(e.type == ElementType.BLANK for e in elements)
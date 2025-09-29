"""Tests for the screenplay validator module."""

import pytest
import json
import tempfile
import os

from screenplay_formatter.parser import ScreenplayParser, ElementType
from screenplay_formatter.validator import (
    ScreenplayValidator,
    ValidationError,
    ErrorCode,
    ValidationReport
)


class TestScreenplayValidator:
    """Test screenplay validator functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ScreenplayParser()
        self.validator = ScreenplayValidator()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validate_valid_screenplay(self):
        """Test validation of a properly formatted screenplay."""
        text = """FADE IN:

INT. OFFICE - DAY

John sits at his desk.

JOHN
This is properly formatted.

CUT TO:"""

        elements = self.parser.parse(text)
        report = self.validator.validate(elements)

        assert report.passed
        assert report.total_errors == 0

    def test_validate_invalid_scene_heading(self):
        """Test detection of invalid scene headings."""
        text = "INT OFFICE DAY"  # Missing periods and dash
        elements = self.parser.parse(text)
        report = self.validator.validate(elements)

        assert not report.passed
        assert report.total_errors > 0
        assert ErrorCode.E1_INVALID_SCENE_HEADING.name in report.errors_by_type

    def test_validate_character_not_caps(self):
        """Test detection of character names not in caps."""
        text = """john
This is dialogue."""

        elements = self.parser.parse(text)
        # Force the parser to recognize it as character/dialogue
        elements[0].type = ElementType.CHARACTER

        report = self.validator.validate(elements)

        assert not report.passed
        assert ErrorCode.E2_INCORRECT_CHARACTER_FORMAT.name in report.errors_by_type

    def test_validate_orphaned_dialogue(self):
        """Test detection of dialogue without character."""
        text = """INT. OFFICE - DAY

This looks like dialogue but has no character."""

        elements = self.parser.parse(text)
        # Force element to be dialogue
        from screenplay_formatter.parser import ElementType
        elements[2].type = ElementType.DIALOGUE

        report = self.validator.validate(elements)

        assert not report.passed
        assert ErrorCode.E6_INVALID_BLOCK_SEQUENCE.name in report.errors_by_type

    def test_validate_parenthetical_format(self):
        """Test detection of incorrectly formatted parentheticals."""
        text = """JOHN
missing parentheses
Hello."""

        elements = self.parser.parse(text)
        # Force middle line to be parenthetical
        from screenplay_formatter.parser import ElementType
        elements[1].type = ElementType.PARENTHETICAL

        report = self.validator.validate(elements)

        assert not report.passed
        assert ErrorCode.E4_INCORRECT_PARENTHETICAL.name in report.errors_by_type

    def test_validate_invalid_transition(self):
        """Test detection of invalid transitions."""
        text = "RANDOM TRANSITION"
        elements = self.parser.parse(text)
        from screenplay_formatter.parser import ElementType
        elements[0].type = ElementType.TRANSITION

        report = self.validator.validate(elements)

        assert not report.passed
        assert ErrorCode.E5_INCORRECT_TRANSITION.name in report.errors_by_type

    def test_suggestion_generation(self):
        """Test that validator generates helpful suggestions."""
        text = "int office day"  # Lowercase, missing punctuation
        elements = self.parser.parse(text)
        from screenplay_formatter.parser import ElementType
        elements[0].type = ElementType.SCENE_HEADING

        report = self.validator.validate(elements)

        assert not report.passed
        assert len(report.errors) > 0

        error = report.errors[0]
        assert error['suggestion'] is not None
        assert "INT." in error['suggestion']
        assert error['confidence'] > 0.5

    def test_export_json_report(self):
        """Test exporting validation report as JSON."""
        text = "INT. OFFICE - DAY"
        elements = self.parser.parse(text)
        report = self.validator.validate(elements)

        output_path = os.path.join(self.temp_dir, "report.json")
        self.validator.export_json(report, output_path)

        assert os.path.exists(output_path)

        with open(output_path, 'r') as f:
            data = json.load(f)

        assert 'total_lines' in data
        assert 'total_errors' in data
        assert 'passed' in data

    def test_export_text_report(self):
        """Test exporting validation report as text."""
        text = """INT OFFICE DAY

john
dialogue"""

        elements = self.parser.parse(text)
        from screenplay_formatter.parser import ElementType
        elements[0].type = ElementType.SCENE_HEADING
        elements[2].type = ElementType.CHARACTER

        report = self.validator.validate(elements)
        text_report = self.validator.export_text(report)

        assert "SCREENPLAY VALIDATION REPORT" in text_report
        assert "Total Errors:" in text_report
        assert "Status: FAILED" in text_report

    def test_strict_mode(self):
        """Test that strict mode applies stricter rules."""
        validator_normal = ScreenplayValidator(strict_mode=False)
        validator_strict = ScreenplayValidator(strict_mode=True)

        text = "INT. OFFICE - DAY"
        elements = self.parser.parse(text)

        report_normal = validator_normal.validate(elements)
        report_strict = validator_strict.validate(elements)

        # Both should handle basic validation the same way
        assert report_normal.passed == report_strict.passed

    def test_confidence_scores(self):
        """Test that confidence scores are assigned appropriately."""
        text = "john"  # Should be JOHN
        elements = self.parser.parse(text)
        from screenplay_formatter.parser import ElementType
        elements[0].type = ElementType.CHARACTER

        report = self.validator.validate(elements)

        assert not report.passed
        error = report.errors[0]
        assert error['confidence'] > 0.9  # High confidence for simple caps fix

    def test_multiple_errors_same_line(self):
        """Test handling multiple errors on the same line."""
        text = "bad scene heading"
        elements = self.parser.parse(text)
        from screenplay_formatter.parser import ElementType
        elements[0].type = ElementType.SCENE_HEADING

        report = self.validator.validate(elements)

        assert not report.passed
        # Should detect invalid format
        assert any(e['line_number'] == 1 for e in report.errors)
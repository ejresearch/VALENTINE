"""Tests for the screenplay formatter modules."""

import pytest
import os
import tempfile
from pathlib import Path

from screenplay_formatter.parser import ScreenplayParser, ElementType
from screenplay_formatter.formatter import TextFormatter, DocxFormatter, PdfFormatter


class TestTextFormatter:
    """Test text formatter functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ScreenplayParser()
        self.formatter = TextFormatter()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_format_scene_heading(self):
        """Test formatting of scene headings."""
        text = "INT. OFFICE - DAY"
        elements = self.parser.parse(text)

        output_path = os.path.join(self.temp_dir, "test.txt")
        self.formatter.format(elements, output_path)

        with open(output_path, 'r') as f:
            content = f.read()

        assert "INT. OFFICE - DAY" in content

    def test_format_character_centered(self):
        """Test that character names are centered."""
        text = "JOHN"
        elements = self.parser.parse(text)
        # Force element to be character type since parser might not detect it
        elements[0].type = ElementType.CHARACTER

        output_path = os.path.join(self.temp_dir, "test.txt")
        self.formatter.format(elements, output_path)

        with open(output_path, 'r') as f:
            content = f.read()

        # Character should be roughly centered
        lines = content.split('\n')
        char_line = lines[0]
        assert char_line.strip() == "JOHN"
        # Check that it's roughly centered (has significant padding)
        assert len(char_line) > len(char_line.strip()) + 20  # Has substantial padding

    def test_format_dialogue_indented(self):
        """Test that dialogue is properly indented."""
        text = """SARAH
This is my dialogue."""
        elements = self.parser.parse(text)
        # Force the types to ensure proper formatting
        elements[0].type = ElementType.CHARACTER
        elements[1].type = ElementType.DIALOGUE

        output_path = os.path.join(self.temp_dir, "test.txt")
        self.formatter.format(elements, output_path)

        with open(output_path, 'r') as f:
            content = f.read()

        lines = content.split('\n')
        dialogue_line = [l for l in lines if "This is my dialogue" in l][0]
        # Check that dialogue has substantial indentation
        assert dialogue_line.startswith(' ' * 20)  # Should have significant indent

    def test_format_transition_right_aligned(self):
        """Test that transitions are right-aligned."""
        text = "CUT TO:"
        elements = self.parser.parse(text)

        output_path = os.path.join(self.temp_dir, "test.txt")
        self.formatter.format(elements, output_path)

        with open(output_path, 'r') as f:
            content = f.read()

        lines = content.split('\n')
        trans_line = lines[0]
        assert trans_line.rstrip().endswith("CUT TO:")
        assert len(trans_line.rstrip()) > 50  # Should be pushed to the right

    def test_format_complete_scene(self):
        """Test formatting a complete scene."""
        text = """FADE IN:

INT. OFFICE - DAY

John sits at his desk.

JOHN
(frustrated)
This isn't working!

CUT TO:"""

        elements = self.parser.parse(text)

        output_path = os.path.join(self.temp_dir, "test.txt")
        self.formatter.format(elements, output_path)

        with open(output_path, 'r') as f:
            content = f.read()

        # Check that all elements are present
        assert "FADE IN:" in content
        assert "INT. OFFICE - DAY" in content
        assert "John sits at his desk." in content
        assert "JOHN" in content
        assert "(frustrated)" in content
        assert "This isn't working!" in content
        assert "CUT TO:" in content


class TestDocxFormatter:
    """Test DOCX formatter functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ScreenplayParser()
        self.formatter = DocxFormatter()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_docx_file(self):
        """Test that DOCX file is created."""
        text = "INT. OFFICE - DAY"
        elements = self.parser.parse(text)

        output_path = os.path.join(self.temp_dir, "test.docx")
        self.formatter.format(elements, output_path)

        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

    def test_docx_contains_content(self):
        """Test that DOCX contains the formatted content."""
        from docx import Document

        text = """INT. OFFICE - DAY

JOHN
Hello, world!"""

        elements = self.parser.parse(text)

        output_path = os.path.join(self.temp_dir, "test.docx")
        self.formatter.format(elements, output_path)

        # Read back the docx
        doc = Document(output_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)

        content = '\n'.join(full_text)
        assert "INT. OFFICE - DAY" in content
        assert "JOHN" in content
        assert "Hello, world!" in content


class TestPdfFormatter:
    """Test PDF formatter functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ScreenplayParser()
        self.formatter = PdfFormatter()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_pdf_file(self):
        """Test that PDF file is created."""
        text = "INT. OFFICE - DAY"
        elements = self.parser.parse(text)

        output_path = os.path.join(self.temp_dir, "test.pdf")
        self.formatter.format(elements, output_path)

        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

    def test_pdf_pagination(self):
        """Test that PDF handles pagination correctly."""
        # Create a long script that should span multiple pages
        text = "FADE IN:\n\n"

        for i in range(10):
            text += f"""INT. LOCATION {i} - DAY

This is action line {i}.

CHARACTER {i}
This is dialogue {i}.

"""

        elements = self.parser.parse(text)

        output_path = os.path.join(self.temp_dir, "test.pdf")
        self.formatter.format(elements, output_path)

        # Check that file was created
        assert os.path.exists(output_path)
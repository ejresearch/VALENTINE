"""Parser module for screenplay elements."""

import re
from enum import Enum, auto
from typing import List, Tuple, Optional
from dataclasses import dataclass


class ElementType(Enum):
    """Types of screenplay elements."""
    SCENE_HEADING = auto()
    ACTION = auto()
    CHARACTER = auto()
    DIALOGUE = auto()
    PARENTHETICAL = auto()
    TRANSITION = auto()
    SHOT = auto()  # New: CLOSE ON, ANGLE ON, etc.
    DUAL_DIALOGUE_LEFT = auto()  # New: Left side of dual dialogue
    DUAL_DIALOGUE_RIGHT = auto()  # New: Right side of dual dialogue
    MONTAGE_BEGIN = auto()
    MONTAGE_END = auto()
    TITLE = auto()
    CHYRON = auto()
    PAGE_BREAK = auto()  # New: Forced page break
    TITLE_PAGE_TITLE = auto()  # New: Screenplay title
    TITLE_PAGE_AUTHOR = auto()  # New: Author name(s)
    TITLE_PAGE_CONTACT = auto()  # New: Contact information
    TITLE_PAGE_CREDIT = auto()  # New: "by", "written by", etc.
    MORE = auto()  # New: (MORE) continuation marker
    SCENE_NUMBER = auto()  # New: Scene numbering
    VFX_SFX = auto()  # New: [SOUND EFFECT] or [VISUAL EFFECT]
    BLANK = auto()
    UNKNOWN = auto()


@dataclass
class ScreenplayElement:
    """Represents a single screenplay element."""
    type: ElementType
    content: str
    line_number: int
    raw_text: str
    scene_number: Optional[int] = None  # For scene numbering support


class ParserState:
    """Tracks parser state for context-aware parsing."""
    def __init__(self):
        self.last_element: Optional[ElementType] = None
        self.in_dialogue_block: bool = False
        self.in_montage: bool = False
        self.expecting_dialogue: bool = False
        self.in_title_page: bool = True  # Start in title page mode
        self.screenplay_started: bool = False  # Track if main screenplay has started


class ScreenplayParser:
    """Parse raw text into structured screenplay elements."""

    SCENE_HEADING_PATTERN = re.compile(
        r"^(INT\.|EXT\.|INT\./EXT\.|I/E\.|INT|EXT)\s+.+(-\s+(DAY|NIGHT|DAWN|DUSK|MORNING|AFTERNOON|EVENING|CONTINUOUS|LATER|MOMENTS LATER|SAME)(\s*\([^)]+\))?)?$",
        re.IGNORECASE
    )

    TRANSITION_PATTERN = re.compile(
        r"^(FADE IN:|FADE OUT\.|FADE TO:|CUT TO:|DISSOLVE TO:|MATCH CUT TO:|JUMP CUT TO:|SMASH CUT TO:|"
        r"TIME CUT:|FADE TO BLACK\.|WIPE TO:|PUSH TO:|IRIS IN\.|IRIS OUT\.|WHIP PAN TO:|"
        r"SPLIT SCREEN|L-CUT|J-CUT|THE END)$",
        re.IGNORECASE
    )

    MONTAGE_BEGIN_PATTERN = re.compile(
        r"^(BEGIN MONTAGE|MONTAGE BEGINS|MONTAGE:|MONTAGE -)$",
        re.IGNORECASE
    )

    MONTAGE_END_PATTERN = re.compile(
        r"^(END MONTAGE|MONTAGE ENDS|END OF MONTAGE)$",
        re.IGNORECASE
    )

    TITLE_PATTERN = re.compile(
        r"^(TITLE:|CHYRON:|SUPER:|SUBTITLE:|CARD:)",
        re.IGNORECASE
    )

    PARENTHETICAL_PATTERN = re.compile(
        r"^\(.+\)$"
    )

    # New: Shot headers pattern
    SHOT_PATTERN = re.compile(
        r"^(CLOSE ON|CLOSEUP ON|CLOSE UP ON|ANGLE ON|WIDE SHOT|WIDER SHOT|WIDEST SHOT|"
        r"NEW ANGLE|ANOTHER ANGLE|REVERSE ANGLE|POV|P\.O\.V\.|INSERT|AERIAL SHOT|"
        r"ESTABLISHING SHOT|MOVING SHOT|TRACKING SHOT|CRANE SHOT|HANDHELD SHOT)[\s:]",
        re.IGNORECASE
    )

    # New: Page break marker
    PAGE_BREAK_PATTERN = re.compile(
        r"^(===|PAGE BREAK|---PAGE---|NEW PAGE)$",
        re.IGNORECASE
    )

    # New: Dual dialogue marker (use ^ for second character in dual dialogue)
    DUAL_DIALOGUE_MARKER = "^"

    # New: Title page patterns
    TITLE_PAGE_TITLE_PATTERN = re.compile(
        r"^TITLE:\s*(.+)$",
        re.IGNORECASE
    )

    TITLE_PAGE_AUTHOR_PATTERN = re.compile(
        r"^AUTHOR:\s*(.+)$",
        re.IGNORECASE
    )

    TITLE_PAGE_CREDIT_PATTERN = re.compile(
        r"^(by|written by|screenplay by|story by)$",
        re.IGNORECASE
    )

    TITLE_PAGE_CONTACT_PATTERN = re.compile(
        r"^CONTACT:\s*(.+)$",
        re.IGNORECASE
    )

    # New: VFX/SFX pattern
    VFX_SFX_PATTERN = re.compile(
        r"^\[(.+)\]$"
    )

    CHARACTER_EXTENSIONS = [
        "(V.O.)", "(O.S.)", "(O.C.)", "(CONT'D)",
        "(V.O./CONT'D)", "(O.S./CONT'D)", "(O.C./CONT'D)"
    ]

    def __init__(self):
        self.state = ParserState()

    def parse(self, text: str) -> List[ScreenplayElement]:
        """Parse text into screenplay elements."""
        if not text:
            return []

        # Clean the text first to remove headers and metadata
        cleaned_text = self._clean_text(text)
        lines = cleaned_text.split('\n')
        elements = []

        for line_num, raw_line in enumerate(lines, 1):
            element = self._parse_line(raw_line, line_num)
            elements.append(element)
            self._update_state(element)

        return self._post_process(elements)

    def _clean_text(self, text: str) -> str:
        """Clean text by removing file headers, metadata, and export information."""
        lines = text.split('\n')
        cleaned_lines = []
        skip_until_content = True

        # Patterns to identify and remove
        header_patterns = [
            r'^[A-Z\s]+ PROJECT',  # "ALPHA PROJECT", "BETA PROJECT", etc.
            r'^[A-Z\s]+ - [A-Z\s]+',  # "PROJECT - FINALIZED SCENES"
            r'^={3,}',  # Lines with 3 or more equals signs
            r'^-{3,}',  # Lines with 3 or more dashes
            r'^Exported:',  # Export timestamps
            r'^Generated:',  # Generation timestamps
            r'^Created:',   # Creation timestamps
            r'^Modified:',  # Modification timestamps
            r'^Last updated:',  # Update timestamps
            r'^\*{3,}$',  # Lines with ONLY 3 or more asterisks (not scene headings)
            r'^#{3,}',   # Lines with 3 or more hash symbols
            r'^ACT \d+, SCENE \d+$',  # "ACT 1, SCENE 1" headers
            r'^SCENE \d+$',  # "SCENE 1" headers
            r'^\[.*\]$',  # Content in square brackets
            r'^Version:',  # Version information
            r'^Draft:',    # Draft information
            r'^\d{4}-\d{2}-\d{2}',  # Date stamps
        ]

        for line in lines:
            stripped = line.strip()

            # Skip empty lines at the beginning
            if skip_until_content and not stripped:
                continue

            # Check if line matches any header pattern (only while still looking for content)
            is_header = False
            if skip_until_content:
                for pattern in header_patterns:
                    if re.match(pattern, stripped, re.IGNORECASE):
                        is_header = True
                        break

            # Skip header lines only at the beginning
            if is_header and skip_until_content:
                continue

            # Check for screenplay content to start including lines
            screenplay_indicators = [
                r'^TITLE:\s*',  # Title page title
                r'^AUTHOR:\s*',  # Title page author
                r'^CONTACT:\s*',  # Title page contact
                r'^(by|written by|screenplay by)$',  # Title page credit
                r'^(FADE IN|FADE OUT|CUT TO|DISSOLVE TO)',
                r'^(INT\.|EXT\.)',
                r'^\**(INT\.|EXT\.)',  # Scene headings with asterisks
                r'^[A-Z][A-Z\s]+$',  # Character names (all caps)
                r'^\s*\([^)]+\)',    # Parentheticals
            ]

            is_screenplay_content = False
            if skip_until_content and stripped:  # Only check if we're still looking for content
                for pattern in screenplay_indicators:
                    if re.match(pattern, stripped, re.IGNORECASE):
                        is_screenplay_content = True
                        skip_until_content = False
                        break

            # If we've found screenplay content, or if we have any non-empty line after skipping headers
            if not skip_until_content or is_screenplay_content:
                skip_until_content = False
                cleaned_lines.append(line)
            elif stripped and not is_header:
                # Non-empty line that doesn't match header pattern - treat as screenplay start
                skip_until_content = False
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def _clean_element_content(self, content: str) -> str:
        """Clean individual element content of common formatting issues."""
        cleaned = content

        # Remove asterisks from scene headings
        if re.match(r'^\*+(INT\.|EXT\.)', cleaned, re.IGNORECASE):
            cleaned = re.sub(r'^\*+', '', cleaned).strip()
            cleaned = re.sub(r'\*+$', '', cleaned).strip()

        # Remove markdown-style bold formatting
        cleaned = re.sub(r'^\*\*(.+)\*\*$', r'\1', cleaned)

        # Remove underscores (markdown italics)
        cleaned = re.sub(r'^_+(.+)_+$', r'\1', cleaned)

        # Remove hash symbols (markdown headers)
        cleaned = re.sub(r'^#+\s*', '', cleaned)

        # Clean up extra spaces
        cleaned = ' '.join(cleaned.split())

        return cleaned

    def _parse_line(self, line: str, line_number: int) -> ScreenplayElement:
        """Parse a single line into a screenplay element."""
        stripped = line.strip()

        if not stripped:
            return ScreenplayElement(ElementType.BLANK, "", line_number, line)

        # Clean up common formatting issues
        cleaned_content = self._clean_element_content(stripped)

        # Check for title page elements ONLY if we're still in title page mode
        if self.state.in_title_page:
            title_match = self.TITLE_PAGE_TITLE_PATTERN.match(cleaned_content)
            if title_match:
                return ScreenplayElement(ElementType.TITLE_PAGE_TITLE, title_match.group(1), line_number, line)

            author_match = self.TITLE_PAGE_AUTHOR_PATTERN.match(cleaned_content)
            if author_match:
                return ScreenplayElement(ElementType.TITLE_PAGE_AUTHOR, author_match.group(1), line_number, line)

            contact_match = self.TITLE_PAGE_CONTACT_PATTERN.match(cleaned_content)
            if contact_match:
                return ScreenplayElement(ElementType.TITLE_PAGE_CONTACT, contact_match.group(1), line_number, line)

            if self.TITLE_PAGE_CREDIT_PATTERN.match(cleaned_content):
                return ScreenplayElement(ElementType.TITLE_PAGE_CREDIT, cleaned_content, line_number, line)

        # Check for VFX/SFX bracketed text
        vfx_match = self.VFX_SFX_PATTERN.match(cleaned_content)
        if vfx_match:
            return ScreenplayElement(ElementType.VFX_SFX, cleaned_content, line_number, line)

        # Check for page breaks
        if self.PAGE_BREAK_PATTERN.match(cleaned_content):
            return ScreenplayElement(ElementType.PAGE_BREAK, cleaned_content, line_number, line)

        # Check for scene heading
        if self.SCENE_HEADING_PATTERN.match(cleaned_content):
            return ScreenplayElement(ElementType.SCENE_HEADING, cleaned_content, line_number, line)

        # Check for shot headers
        if self.SHOT_PATTERN.match(cleaned_content):
            return ScreenplayElement(ElementType.SHOT, cleaned_content, line_number, line)

        # Check for transitions
        if self.TRANSITION_PATTERN.match(cleaned_content):
            return ScreenplayElement(ElementType.TRANSITION, cleaned_content, line_number, line)

        # Check for montage markers
        if self.MONTAGE_BEGIN_PATTERN.match(cleaned_content):
            return ScreenplayElement(ElementType.MONTAGE_BEGIN, cleaned_content, line_number, line)

        if self.MONTAGE_END_PATTERN.match(cleaned_content):
            return ScreenplayElement(ElementType.MONTAGE_END, cleaned_content, line_number, line)

        # Check for titles/chyrons
        if self.TITLE_PATTERN.match(cleaned_content):
            return ScreenplayElement(ElementType.TITLE, cleaned_content, line_number, line)

        # Check for parentheticals
        if self.PARENTHETICAL_PATTERN.match(cleaned_content) and self.state.in_dialogue_block:
            return ScreenplayElement(ElementType.PARENTHETICAL, cleaned_content, line_number, line)

        # Check for dual dialogue character (marked with ^ at start)
        if cleaned_content.startswith(self.DUAL_DIALOGUE_MARKER):
            clean_name = cleaned_content[1:].strip()
            if self._is_character_name(clean_name):
                return ScreenplayElement(ElementType.DUAL_DIALOGUE_RIGHT, clean_name, line_number, line)

        # Check for character names
        if self._is_character_name(cleaned_content):
            return ScreenplayElement(ElementType.CHARACTER, cleaned_content, line_number, line)

        # Check if we're expecting dialogue
        if self.state.expecting_dialogue or self.state.in_dialogue_block:
            # If it's not all caps and not a parenthetical, it's probably dialogue
            if not cleaned_content.isupper() and not self.PARENTHETICAL_PATTERN.match(cleaned_content):
                return ScreenplayElement(ElementType.DIALOGUE, cleaned_content, line_number, line)

        # Default to action
        return ScreenplayElement(ElementType.ACTION, cleaned_content, line_number, line)

    def _is_character_name(self, text: str) -> bool:
        """Check if text is likely a character name."""
        # Remove extensions
        clean_text = text
        for ext in self.CHARACTER_EXTENSIONS:
            clean_text = clean_text.replace(ext, "").strip()

        # Character names are typically:
        # - ALL CAPS
        # - Relatively short (1-3 words usually)
        # - Not a scene heading or transition
        # - May end with a colon (optional)

        if clean_text.endswith(':'):
            clean_text = clean_text[:-1].strip()

        if not clean_text:
            return False

        # Must be mostly uppercase
        if not clean_text.isupper():
            return False

        # Should be relatively short
        words = clean_text.split()
        if len(words) > 4:
            return False

        # Not a scene heading or transition
        if self.SCENE_HEADING_PATTERN.match(text):  # Check original text
            return False
        if self.TRANSITION_PATTERN.match(text):  # Check original text
            return False

        # Character names are typically standalone ALL CAPS lines
        # that are not too long and don't look like action
        if len(clean_text) < 50:  # Character names are usually short
            return True

        return False

    def _update_state(self, element: ScreenplayElement):
        """Update parser state based on parsed element."""
        # Exit title page mode once we hit screenplay elements
        if element.type in [ElementType.SCENE_HEADING, ElementType.TRANSITION, ElementType.ACTION]:
            if element.type == ElementType.TRANSITION or element.type == ElementType.SCENE_HEADING:
                self.state.in_title_page = False
                self.state.screenplay_started = True

        if element.type == ElementType.CHARACTER:
            self.state.in_dialogue_block = True
            self.state.expecting_dialogue = True
        elif element.type == ElementType.DIALOGUE:
            self.state.expecting_dialogue = False
            # Stay in dialogue block for multi-line dialogue
        elif element.type == ElementType.PARENTHETICAL:
            self.state.expecting_dialogue = True
        elif element.type == ElementType.BLANK:
            # Blank line after dialogue keeps us in dialogue block
            if self.state.last_element == ElementType.DIALOGUE:
                self.state.in_dialogue_block = True
                self.state.expecting_dialogue = False
            else:
                self.state.in_dialogue_block = False
                self.state.expecting_dialogue = False
        elif element.type in [ElementType.ACTION, ElementType.SCENE_HEADING, ElementType.TRANSITION]:
            self.state.in_dialogue_block = False
            self.state.expecting_dialogue = False
        elif element.type == ElementType.MONTAGE_BEGIN:
            self.state.in_montage = True
        elif element.type == ElementType.MONTAGE_END:
            self.state.in_montage = False

        if element.type != ElementType.BLANK:
            self.state.last_element = element.type

    def _post_process(self, elements: List[ScreenplayElement]) -> List[ScreenplayElement]:
        """Post-process elements to fix common parsing issues."""
        processed = []
        scene_number = 0

        for i, element in enumerate(elements):
            # Fix misidentified dialogue that should be action
            if element.type == ElementType.DIALOGUE:
                prev_elem = elements[i-1] if i > 0 else None
                if prev_elem and prev_elem.type not in [ElementType.CHARACTER, ElementType.PARENTHETICAL, ElementType.DIALOGUE]:
                    element.type = ElementType.ACTION

            # Fix character names that might be action
            if element.type == ElementType.CHARACTER:
                next_elem = elements[i+1] if i < len(elements) - 1 else None
                if next_elem and next_elem.type not in [ElementType.DIALOGUE, ElementType.PARENTHETICAL, ElementType.BLANK]:
                    # Might be misidentified action
                    if not any(ext in element.content.upper() for ext in self.CHARACTER_EXTENSIONS):
                        element.type = ElementType.ACTION

            # Add scene numbers to scene headings
            if element.type == ElementType.SCENE_HEADING:
                scene_number += 1
                element.scene_number = scene_number

            processed.append(element)

        return processed

    def enable_scene_numbering(self) -> None:
        """Enable scene numbering for parsed elements."""
        # This is handled automatically in _post_process now
        pass
"""Meta-comment detection and removal utility for screenplays."""

import re
from typing import List, Tuple
from dataclasses import dataclass

from .parser import ScreenplayElement, ElementType


@dataclass
class RemovedComment:
    """Record of a removed meta-comment."""
    line_number: int
    element_type: ElementType
    original_content: str
    cleaned_content: str
    comment_text: str


class MetaCommentRemover:
    """Remove meta-comments and production notes from spec scripts."""

    # Pattern for meta-comments
    META_COMMENT_PATTERN = re.compile(
        r'\[(?:NOTE|TODO|FIXME|DECIDE|MAYBE|REMINDER|TBD|SHOOT|CUT|EDIT|REVIEW|CHECK|QUESTION|'
        r'Q:|TEMP|PLACEHOLDER|TK|XXX|HACK|BUG|WARNING).*?\]',
        re.IGNORECASE
    )

    # Additional patterns for common production notes
    PRODUCTION_NOTE_PATTERNS = [
        re.compile(r'\((?:NOTE|TODO|FIXME):[^)]+\)', re.IGNORECASE),  # (NOTE: something)
        re.compile(r'//.*?(?:\n|$)'),  # // comments
        re.compile(r'#.*?(?:\n|$)'),  # # comments (but preserve #SCENE markers in context)
    ]

    def __init__(self):
        """Initialize meta-comment remover."""
        self.removed_comments: List[RemovedComment] = []

    def remove_meta_comments(self, elements: List[ScreenplayElement]) -> List[ScreenplayElement]:
        """
        Remove meta-comments from screenplay elements.

        Args:
            elements: Original screenplay elements

        Returns:
            Cleaned elements with meta-comments removed
        """
        self.removed_comments = []
        cleaned_elements = []

        for element in elements:
            # Only process certain element types
            if element.type in [ElementType.ACTION, ElementType.DIALOGUE,
                              ElementType.SCENE_HEADING, ElementType.PARENTHETICAL]:
                cleaned_content, comments_found = self._clean_content(element.content)

                # Record removals
                if comments_found:
                    for comment in comments_found:
                        self.removed_comments.append(RemovedComment(
                            line_number=element.line_number,
                            element_type=element.type,
                            original_content=element.content,
                            cleaned_content=cleaned_content,
                            comment_text=comment
                        ))

                # Only keep element if it has content after cleaning
                if cleaned_content.strip():
                    cleaned_element = ScreenplayElement(
                        type=element.type,
                        content=cleaned_content,
                        line_number=element.line_number,
                        raw_line=element.raw_line
                    )
                    cleaned_elements.append(cleaned_element)
                # If element is now empty, skip it (effectively removing it)

            else:
                # Keep other elements as-is
                cleaned_elements.append(element)

        return cleaned_elements

    def _clean_content(self, content: str) -> Tuple[str, List[str]]:
        """
        Clean meta-comments from content.

        Args:
            content: Original content string

        Returns:
            Tuple of (cleaned_content, list_of_removed_comments)
        """
        comments_found = []
        cleaned = content

        # Find and remove bracketed meta-comments
        matches = self.META_COMMENT_PATTERN.findall(cleaned)
        if matches:
            comments_found.extend(matches)
            cleaned = self.META_COMMENT_PATTERN.sub('', cleaned)

        # Check other production note patterns
        for pattern in self.PRODUCTION_NOTE_PATTERNS:
            matches = pattern.findall(cleaned)
            if matches:
                # Filter out false positives (e.g., actual scene markers)
                for match in matches:
                    if not self._is_false_positive(match):
                        comments_found.append(match)
                        cleaned = pattern.sub('', cleaned)

        # Clean up extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Multiple spaces to single space
        cleaned = cleaned.strip()

        return cleaned, comments_found

    def _is_false_positive(self, text: str) -> bool:
        """
        Check if detected comment is actually valid screenplay content.

        Args:
            text: Detected comment text

        Returns:
            True if this is NOT a meta-comment (false positive)
        """
        # Allow actual screenplay elements that might match patterns
        false_positive_markers = [
            'SCENE',
            'ACT',
            'SEQUENCE'
        ]

        text_upper = text.upper()
        return any(marker in text_upper for marker in false_positive_markers)

    def get_removal_report(self) -> str:
        """
        Generate a report of removed meta-comments.

        Returns:
            Formatted report string
        """
        if not self.removed_comments:
            return "No meta-comments found."

        lines = ["Meta-Comment Removal Report", "=" * 60, ""]
        lines.append(f"Total meta-comments removed: {len(self.removed_comments)}")
        lines.append("")

        # Group by element type
        by_type = {}
        for removal in self.removed_comments:
            type_name = removal.element_type.name
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append(removal)

        for element_type, removals in sorted(by_type.items()):
            lines.append(f"{element_type}: {len(removals)} comments removed")

        lines.append("")
        lines.append("Detailed Removals:")
        lines.append("-" * 60)

        for removal in self.removed_comments:
            lines.append(f"Line {removal.line_number} ({removal.element_type.name}):")
            lines.append(f"  Removed: {removal.comment_text}")
            lines.append(f"  Before: {removal.original_content[:80]}...")
            lines.append(f"  After:  {removal.cleaned_content[:80]}...")
            lines.append("")

        return "\n".join(lines)

    def has_meta_comments(self, elements: List[ScreenplayElement]) -> bool:
        """
        Check if screenplay contains meta-comments.

        Args:
            elements: Screenplay elements to check

        Returns:
            True if meta-comments are found
        """
        for element in elements:
            if element.type in [ElementType.ACTION, ElementType.DIALOGUE,
                              ElementType.SCENE_HEADING, ElementType.PARENTHETICAL]:
                if self.META_COMMENT_PATTERN.search(element.content):
                    return True

                # Check other patterns
                for pattern in self.PRODUCTION_NOTE_PATTERNS:
                    matches = pattern.findall(element.content)
                    if matches and not all(self._is_false_positive(m) for m in matches):
                        return True

        return False

    def preview_removal(self, elements: List[ScreenplayElement]) -> List[str]:
        """
        Preview what would be removed without actually modifying elements.

        Args:
            elements: Screenplay elements

        Returns:
            List of meta-comments that would be removed
        """
        preview_comments = []

        for element in elements:
            if element.type in [ElementType.ACTION, ElementType.DIALOGUE,
                              ElementType.SCENE_HEADING, ElementType.PARENTHETICAL]:
                _, comments = self._clean_content(element.content)
                preview_comments.extend(comments)

        return preview_comments

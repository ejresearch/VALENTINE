"""Character name unification utility for screenplays."""

import re
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict

from .parser import ScreenplayElement, ElementType


@dataclass
class CharacterVariant:
    """Represents a variant of a character name."""
    canonical: str  # The canonical (preferred) form
    variants: Set[str]  # All variations found
    occurrences: int  # Total number of appearances
    line_numbers: List[int]  # Where each variant appears


class CharacterNameUnifier:
    """Unify character name variations in a screenplay."""

    def __init__(self):
        """Initialize character name unifier."""
        self.character_map: Dict[str, CharacterVariant] = {}

    def analyze_characters(self, elements: List[ScreenplayElement]) -> Dict[str, CharacterVariant]:
        """
        Analyze all character names and identify variations.

        Args:
            elements: List of screenplay elements

        Returns:
            Dictionary mapping canonical names to CharacterVariant objects
        """
        # First pass: collect all character names
        character_instances = defaultdict(list)

        for element in elements:
            if element.type == ElementType.CHARACTER:
                # Strip extensions like (O.S.), (V.O.), (CONT'D)
                base_name = self._extract_base_name(element.content)
                base_name_upper = base_name.upper()

                character_instances[base_name_upper].append({
                    'line': element.line_number,
                    'form': base_name
                })

        # Second pass: group related names and identify canonical form
        self.character_map = {}
        processed_names = set()

        for canonical_name, instances in character_instances.items():
            if canonical_name in processed_names:
                continue

            # Collect all variants
            variants = set(inst['form'] for inst in instances)
            line_numbers = [inst['line'] for inst in instances]

            # Check for related names (e.g., JESS and JESSICA)
            related_names = self._find_related_names(canonical_name, character_instances.keys())

            # Merge related names
            for related in related_names:
                if related != canonical_name and related not in processed_names:
                    variants.update(inst['form'] for inst in character_instances[related])
                    line_numbers.extend(inst['line'] for inst in character_instances[related])
                    processed_names.add(related)

            # Determine canonical form (prefer full name or most common form)
            canonical_form = self._determine_canonical_form(variants)

            self.character_map[canonical_form] = CharacterVariant(
                canonical=canonical_form,
                variants=variants,
                occurrences=len(line_numbers),
                line_numbers=sorted(line_numbers)
            )

            processed_names.add(canonical_name)

        return self.character_map

    def _extract_base_name(self, character_line: str) -> str:
        """Extract base character name without extensions."""
        # Remove (O.S.), (V.O.), (CONT'D), etc.
        base_name = re.sub(r'\s*\([^)]+\)\s*$', '', character_line)
        return base_name.strip()

    def _find_related_names(self, name: str, all_names: List[str]) -> List[str]:
        """
        Find character names that might be variations of the same character.

        Examples:
            JESS and JESSICA
            MIKE and MICHAEL
            BOB and ROBERT
        """
        related = []

        for other_name in all_names:
            if other_name == name:
                continue

            # Check if one name is substring of another
            if name in other_name or other_name in name:
                # Additional check: names should share at least 3 characters
                if len(set(name) & set(other_name)) >= 3:
                    related.append(other_name)

        return related

    def _determine_canonical_form(self, variants: Set[str]) -> str:
        """
        Determine the canonical form from variants.

        Prefers:
        1. Longest name (JESSICA over JESS)
        2. All caps version
        3. First occurrence if tied
        """
        # Convert to list and sort by length (descending), then alphabetically
        sorted_variants = sorted(variants, key=lambda x: (-len(x), x))

        # Prefer all-caps versions
        all_caps = [v for v in sorted_variants if v.isupper()]
        if all_caps:
            return all_caps[0]

        # Otherwise return longest
        return sorted_variants[0]

    def unify_characters(self, elements: List[ScreenplayElement]) -> List[ScreenplayElement]:
        """
        Apply character name unification to screenplay elements.

        Args:
            elements: Original screenplay elements

        Returns:
            Modified elements with unified character names
        """
        # First analyze if not done yet
        if not self.character_map:
            self.analyze_characters(elements)

        # Create mapping from variant to canonical
        variant_to_canonical = {}
        for char_var in self.character_map.values():
            for variant in char_var.variants:
                variant_to_canonical[variant.upper()] = char_var.canonical

        # Apply unification
        unified_elements = []
        for element in elements:
            if element.type == ElementType.CHARACTER:
                base_name = self._extract_base_name(element.content)

                # Get canonical name
                canonical = variant_to_canonical.get(base_name.upper(), base_name.upper())

                # Reconstruct with extensions if present
                extensions = self._extract_extensions(element.content)
                new_content = canonical + extensions

                # Create new element with unified name
                unified_element = ScreenplayElement(
                    type=element.type,
                    content=new_content,
                    line_number=element.line_number,
                    raw_line=element.raw_line
                )
                unified_elements.append(unified_element)
            else:
                unified_elements.append(element)

        return unified_elements

    def _extract_extensions(self, character_line: str) -> str:
        """Extract extensions like (O.S.), (V.O.), (CONT'D)."""
        match = re.search(r'\s*(\([^)]+\))\s*$', character_line)
        if match:
            return ' ' + match.group(1)
        return ''

    def get_unification_report(self) -> str:
        """
        Generate a human-readable report of character name unifications.

        Returns:
            Formatted report string
        """
        if not self.character_map:
            return "No character analysis performed yet."

        lines = ["Character Name Unification Report", "=" * 50, ""]

        # Sort by occurrence count (descending)
        sorted_chars = sorted(
            self.character_map.values(),
            key=lambda x: x.occurrences,
            reverse=True
        )

        for char in sorted_chars:
            lines.append(f"Character: {char.canonical}")
            lines.append(f"  Occurrences: {char.occurrences}")

            if len(char.variants) > 1:
                lines.append(f"  Variants found: {', '.join(sorted(char.variants))}")
                lines.append(f"  → Will unify to: {char.canonical}")
            else:
                lines.append("  No variants (consistent naming)")

            lines.append("")

        return "\n".join(lines)

    def get_inconsistent_characters(self) -> Dict[str, CharacterVariant]:
        """
        Get only characters with naming inconsistencies.

        Returns:
            Dictionary of characters with multiple variants
        """
        return {
            name: variant
            for name, variant in self.character_map.items()
            if len(variant.variants) > 1
        }

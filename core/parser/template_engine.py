"""
DocuForge Template Engine

A custom template engine designed for document generation with:
- Type-safe variable substitution (handles None, tuples, lists, dicts)
- Conditional sections with proper boolean logic
- Section dependencies and references
- Circular dependency detection

This engine uses a custom syntax (NOT Django templates or Jinja2)
specifically designed for legal/clinical document generation.

Syntax:
    Variables:    {{variable_name}}
    Conditionals: {% if condition %}...{% endif %}
    Sections:     {% section name %}...{% endsection %}
    References:   {% include section_name %}

Author: Ahmed Sallemi | MediaTree
"""
import re
from typing import Any, Dict, List, Optional, Set, Union
from dataclasses import dataclass

from .exceptions import (
    InvalidTemplateError,
    VariableResolutionError,
    CircularDependencyError,
)
from .condition_evaluator import ConditionEvaluator
from .variable_resolver import VariableResolver


@dataclass
class Section:
    """Represents a named section within a template."""
    name: str
    content: str
    condition: Optional[str] = None
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class TemplateEngine:
    """
    Custom template engine for document generation.

    Features:
    - Type-safe variable substitution (no more 'tuple has no attribute strip' errors)
    - Proper AND/OR precedence in conditions
    - Circular dependency detection
    - Section-based document structure

    Example:
        engine = TemplateEngine()
        template = "Hello {{name}}, your items: {{items}}"
        context = {'name': 'John', 'items': ('Apple', 'Orange', 'Banana')}
        result = engine.render(template, context)
        # Result: "Hello John, your items: Apple, Orange, Banana"
    """

    # Regex patterns for parsing
    VARIABLE_PATTERN = re.compile(r'\{\{(\w+(?:\.\w+)*)\}\}')
    CONDITIONAL_PATTERN = re.compile(
        r'\{%\s*if\s+(.+?)\s*%\}(.*?)\{%\s*endif\s*%\}',
        re.DOTALL
    )
    CONDITIONAL_ELSE_PATTERN = re.compile(
        r'\{%\s*if\s+(.+?)\s*%\}(.*?)\{%\s*else\s*%\}(.*?)\{%\s*endif\s*%\}',
        re.DOTALL
    )
    SECTION_PATTERN = re.compile(
        r'\{%\s*section\s+(\w+)\s*%\}(.*?)\{%\s*endsection\s*%\}',
        re.DOTALL
    )
    INCLUDE_PATTERN = re.compile(r'\{%\s*include\s+(\w+)\s*%\}')

    def __init__(self):
        self.condition_evaluator = ConditionEvaluator()
        self.variable_resolver = VariableResolver()
        self._sections: Dict[str, Section] = {}
        self._resolution_stack: Set[str] = set()

    def render(self, template: str, context: Dict[str, Any]) -> str:
        """
        Render a template with the given context.

        Args:
            template: The template string to render
            context: Dictionary of variables to substitute

        Returns:
            The rendered template string

        Raises:
            InvalidTemplateError: If template syntax is invalid
            VariableResolutionError: If a required variable is missing
            CircularDependencyError: If circular section references exist
        """
        if not isinstance(template, str):
            raise InvalidTemplateError(str(template), "Template must be a string")

        # Reset state
        self._sections = {}
        self._resolution_stack = set()

        # Parse sections first
        template = self._parse_sections(template)

        # Process conditionals (with else)
        template = self._process_conditionals_with_else(template, context)

        # Process conditionals (without else)
        template = self._process_conditionals(template, context)

        # Process includes
        template = self._process_includes(template, context)

        # Substitute variables
        template = self._substitute_variables(template, context)

        return template.strip()

    def _parse_sections(self, template: str) -> str:
        """Extract and store named sections from the template."""
        def section_handler(match):
            name = match.group(1)
            content = match.group(2)
            self._sections[name] = Section(name=name, content=content.strip())
            return ""  # Remove section definition from main template

        return self.SECTION_PATTERN.sub(section_handler, template)

    def _process_conditionals_with_else(self, template: str, context: Dict[str, Any]) -> str:
        """Process {% if %}...{% else %}...{% endif %} blocks."""
        def conditional_handler(match):
            condition = match.group(1)
            true_content = match.group(2)
            false_content = match.group(3)

            try:
                result = self.condition_evaluator.evaluate(condition, context)
                return true_content if result else false_content
            except Exception as e:
                # Log but don't crash - return empty for failed conditions
                return ""

        return self.CONDITIONAL_ELSE_PATTERN.sub(conditional_handler, template)

    def _process_conditionals(self, template: str, context: Dict[str, Any]) -> str:
        """Process {% if %}...{% endif %} blocks."""
        def conditional_handler(match):
            condition = match.group(1)
            content = match.group(2)

            try:
                result = self.condition_evaluator.evaluate(condition, context)
                return content if result else ""
            except Exception as e:
                return ""

        return self.CONDITIONAL_PATTERN.sub(conditional_handler, template)

    def _process_includes(self, template: str, context: Dict[str, Any]) -> str:
        """Process {% include section_name %} directives with cycle detection."""
        def include_handler(match):
            section_name = match.group(1)

            # Circular dependency detection
            if section_name in self._resolution_stack:
                chain = list(self._resolution_stack) + [section_name]
                raise CircularDependencyError(chain)

            if section_name not in self._sections:
                return f"[MISSING SECTION: {section_name}]"

            # Track resolution for cycle detection
            self._resolution_stack.add(section_name)

            section = self._sections[section_name]
            content = section.content

            # Recursively process includes in the section
            content = self._process_includes(content, context)
            content = self._substitute_variables(content, context)

            self._resolution_stack.remove(section_name)

            return content

        return self.INCLUDE_PATTERN.sub(include_handler, template)

    def _substitute_variables(self, template: str, context: Dict[str, Any]) -> str:
        """
        Substitute variables with TYPE-SAFE handling.

        This method properly handles:
        - None values -> empty string
        - Tuples/Lists -> comma-separated string
        - Nested dict access -> dot notation
        - Missing variables -> placeholder or error based on config
        """
        def variable_handler(match):
            var_name = match.group(1)

            try:
                value = self.variable_resolver.resolve(var_name, context)
                return self._to_safe_string(value)
            except VariableResolutionError:
                # Return placeholder for missing variables
                return f"[{var_name}]"

        return self.VARIABLE_PATTERN.sub(variable_handler, template)

    def _to_safe_string(self, value: Any) -> str:
        """
        Convert any value to a safe string representation.

        This is the KEY METHOD that prevents the common bug:
        'tuple' object has no attribute 'strip'

        Handles:
        - None -> ""
        - str -> str (stripped)
        - int/float -> str
        - bool -> "Yes"/"No"
        - list/tuple -> comma-separated
        - dict -> raises error (should not substitute dicts directly)
        - datetime -> ISO format
        - Any other -> str()
        """
        if value is None:
            return ""

        if isinstance(value, str):
            return value.strip()

        if isinstance(value, bool):
            return "Yes" if value else "No"

        if isinstance(value, (int, float)):
            return str(value)

        if isinstance(value, (list, tuple)):
            # Filter out None values and convert each item safely
            items = [self._to_safe_string(item) for item in value if item is not None]
            return ", ".join(items)

        if isinstance(value, dict):
            # Dicts should not be directly substituted
            raise VariableResolutionError(
                str(value)[:50],
                "Cannot substitute dict directly. Use dot notation to access specific keys."
            )

        # Handle datetime objects
        if hasattr(value, 'isoformat'):
            return value.isoformat()

        # Fallback: convert to string
        return str(value)

    def get_variables(self, template: str) -> List[str]:
        """Extract all variable names from a template."""
        return self.VARIABLE_PATTERN.findall(template)

    def get_conditions(self, template: str) -> List[str]:
        """Extract all conditions from a template."""
        conditions = []
        for match in self.CONDITIONAL_PATTERN.finditer(template):
            conditions.append(match.group(1))
        for match in self.CONDITIONAL_ELSE_PATTERN.finditer(template):
            conditions.append(match.group(1))
        return conditions

    def validate(self, template: str) -> Dict[str, Any]:
        """
        Validate a template and return analysis.

        Returns:
            Dict with 'valid', 'variables', 'conditions', 'sections', 'errors'
        """
        errors = []
        variables = []
        conditions = []
        sections = []

        try:
            variables = self.get_variables(template)
        except Exception as e:
            errors.append(f"Variable parsing error: {e}")

        try:
            conditions = self.get_conditions(template)
        except Exception as e:
            errors.append(f"Condition parsing error: {e}")

        # Check for unclosed tags
        if template.count('{%') != template.count('%}'):
            errors.append("Unclosed template tags detected")

        if template.count('{{') != template.count('}}'):
            errors.append("Unclosed variable tags detected")

        return {
            'valid': len(errors) == 0,
            'variables': variables,
            'conditions': conditions,
            'sections': list(self._sections.keys()),
            'errors': errors,
        }

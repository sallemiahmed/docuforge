"""
Tests for DocuForge Template Engine

These tests specifically cover edge cases that commonly cause bugs
in custom template engines:
- Type coercion issues (None, tuple, list)
- Nested variable resolution
- Circular dependency detection

Author: Ahmed Sallemi | MediaTree
"""
import pytest
from core.parser import (
    TemplateEngine,
    VariableResolutionError,
    CircularDependencyError,
    InvalidTemplateError,
)


class TestTypeSafeSubstitution:
    """
    Tests for type-safe variable substitution.

    These tests verify that the engine handles all data types correctly,
    preventing the common bug: "'tuple' object has no attribute 'strip'"
    """

    def setup_method(self):
        self.engine = TemplateEngine()

    def test_string_substitution(self):
        """Basic string substitution works correctly."""
        template = "Hello {{name}}"
        context = {'name': 'John'}
        result = self.engine.render(template, context)
        assert result == "Hello John"

    def test_none_value_becomes_empty_string(self):
        """None values should render as empty string, not 'None'."""
        template = "Name: {{name}}, Notes: {{notes}}"
        context = {'name': 'John', 'notes': None}
        result = self.engine.render(template, context)
        assert result == "Name: John, Notes:"

    def test_tuple_values_are_comma_joined(self):
        """
        Tuple values should be joined with commas.

        This prevents: "'tuple' object has no attribute 'strip'"
        """
        template = "Parties: {{parties}}"
        context = {'parties': ('Alice', 'Bob', 'Charlie')}
        result = self.engine.render(template, context)
        assert result == "Parties: Alice, Bob, Charlie"

    def test_list_values_are_comma_joined(self):
        """List values should be joined with commas."""
        template = "Items: {{items}}"
        context = {'items': ['Apple', 'Orange', 'Banana']}
        result = self.engine.render(template, context)
        assert result == "Items: Apple, Orange, Banana"

    def test_nested_list_with_none_values(self):
        """Lists containing None values should filter them out."""
        template = "Values: {{values}}"
        context = {'values': ['A', None, 'B', None, 'C']}
        result = self.engine.render(template, context)
        assert result == "Values: A, B, C"

    def test_integer_substitution(self):
        """Integer values should be converted to strings."""
        template = "Age: {{age}} years old"
        context = {'age': 25}
        result = self.engine.render(template, context)
        assert result == "Age: 25 years old"

    def test_float_substitution(self):
        """Float values should be converted to strings."""
        template = "Price: ${{price}}"
        context = {'price': 19.99}
        result = self.engine.render(template, context)
        assert result == "Price: $19.99"

    def test_boolean_true_becomes_yes(self):
        """True boolean values should render as 'Yes'."""
        template = "Active: {{is_active}}"
        context = {'is_active': True}
        result = self.engine.render(template, context)
        assert result == "Active: Yes"

    def test_boolean_false_becomes_no(self):
        """False boolean values should render as 'No'."""
        template = "Active: {{is_active}}"
        context = {'is_active': False}
        result = self.engine.render(template, context)
        assert result == "Active: No"

    def test_missing_variable_shows_placeholder(self):
        """Missing variables should show placeholder, not crash."""
        template = "Hello {{name}}, your ID is {{user_id}}"
        context = {'name': 'John'}  # Missing 'user_id'
        result = self.engine.render(template, context)
        assert result == "Hello John, your ID is [user_id]"

    def test_whitespace_is_stripped(self):
        """String values should have whitespace stripped."""
        template = "Name: {{name}}"
        context = {'name': '  John Doe  '}
        result = self.engine.render(template, context)
        assert result == "Name: John Doe"


class TestNestedVariableResolution:
    """Tests for dot notation variable access."""

    def setup_method(self):
        self.engine = TemplateEngine()

    def test_nested_dict_access(self):
        """Can access nested dict values with dot notation."""
        template = "Welcome {{user.profile.name}}"
        context = {
            'user': {
                'profile': {
                    'name': 'John Doe'
                }
            }
        }
        result = self.engine.render(template, context)
        assert result == "Welcome John Doe"

    def test_deeply_nested_access(self):
        """Can access deeply nested values."""
        template = "City: {{company.address.city}}"
        context = {
            'company': {
                'address': {
                    'city': 'New York'
                }
            }
        }
        result = self.engine.render(template, context)
        assert result == "City: New York"

    def test_missing_nested_key_returns_placeholder(self):
        """Missing nested keys return placeholder."""
        template = "Email: {{user.contact.email}}"
        context = {'user': {'name': 'John'}}  # Missing contact.email
        result = self.engine.render(template, context)
        assert result == "Email: [user.contact.email]"


class TestConditionalRendering:
    """Tests for conditional template blocks."""

    def setup_method(self):
        self.engine = TemplateEngine()

    def test_simple_if_true(self):
        """True condition includes content."""
        template = "Hello{% if show_greeting %} World{% endif %}"
        context = {'show_greeting': True}
        result = self.engine.render(template, context)
        assert result == "Hello World"

    def test_simple_if_false(self):
        """False condition excludes content."""
        template = "Hello{% if show_greeting %} World{% endif %}"
        context = {'show_greeting': False}
        result = self.engine.render(template, context)
        assert result == "Hello"

    def test_if_else_true_branch(self):
        """If-else shows true branch when condition is true."""
        template = "{% if is_admin %}Admin{% else %}User{% endif %}"
        context = {'is_admin': True}
        result = self.engine.render(template, context)
        assert result == "Admin"

    def test_if_else_false_branch(self):
        """If-else shows false branch when condition is false."""
        template = "{% if is_admin %}Admin{% else %}User{% endif %}"
        context = {'is_admin': False}
        result = self.engine.render(template, context)
        assert result == "User"

    def test_conditional_with_comparison(self):
        """Conditionals work with comparison operators."""
        template = "{% if age >= 18 %}Adult{% else %}Minor{% endif %}"
        context = {'age': 25}
        result = self.engine.render(template, context)
        assert result == "Adult"

    def test_conditional_with_and(self):
        """Conditionals work with AND operator."""
        template = "{% if age >= 18 AND has_consent %}Proceed{% endif %}"
        context = {'age': 25, 'has_consent': True}
        result = self.engine.render(template, context)
        assert result == "Proceed"

    def test_conditional_with_or(self):
        """Conditionals work with OR operator."""
        template = "{% if is_vip OR is_employee %}Access Granted{% endif %}"
        context = {'is_vip': False, 'is_employee': True}
        result = self.engine.render(template, context)
        assert result == "Access Granted"


class TestSectionAndIncludes:
    """Tests for section definitions and includes."""

    def setup_method(self):
        self.engine = TemplateEngine()

    def test_section_definition_and_include(self):
        """Sections can be defined and included."""
        template = """
{% section header %}Welcome to our service{% endsection %}
{% section footer %}Thank you for your business{% endsection %}
{% include header %}

Main content here

{% include footer %}
"""
        result = self.engine.render(template, {})
        assert "Welcome to our service" in result
        assert "Main content here" in result
        assert "Thank you for your business" in result

    def test_circular_dependency_detection(self):
        """Circular section references should be detected."""
        template = """
{% section a %}See {% include b %}{% endsection %}
{% section b %}See {% include a %}{% endsection %}
{% include a %}
"""
        with pytest.raises(CircularDependencyError):
            self.engine.render(template, {})

    def test_missing_section_shows_placeholder(self):
        """Missing sections show placeholder."""
        template = "{% include nonexistent %}"
        result = self.engine.render(template, {})
        assert "[MISSING SECTION: nonexistent]" in result


class TestTemplateValidation:
    """Tests for template validation."""

    def setup_method(self):
        self.engine = TemplateEngine()

    def test_valid_template(self):
        """Valid templates pass validation."""
        template = "Hello {{name}}, {% if show %}World{% endif %}"
        result = self.engine.validate(template)
        assert result['valid'] is True
        assert 'name' in result['variables']

    def test_unclosed_variable_tag(self):
        """Unclosed variable tags are detected."""
        template = "Hello {{name"
        result = self.engine.validate(template)
        assert result['valid'] is False

    def test_extract_variables(self):
        """All variables are extracted correctly."""
        template = "{{a}} and {{b}} and {{c.d}}"
        variables = self.engine.get_variables(template)
        assert 'a' in variables
        assert 'b' in variables
        assert 'c.d' in variables


class TestEdgeCases:
    """Edge case tests."""

    def setup_method(self):
        self.engine = TemplateEngine()

    def test_empty_template(self):
        """Empty template returns empty string."""
        result = self.engine.render("", {})
        assert result == ""

    def test_template_with_no_variables(self):
        """Template with no variables renders unchanged."""
        template = "Hello World"
        result = self.engine.render(template, {})
        assert result == "Hello World"

    def test_empty_context(self):
        """Empty context shows placeholders for variables."""
        template = "Hello {{name}}"
        result = self.engine.render(template, {})
        assert result == "Hello [name]"

    def test_multiple_same_variables(self):
        """Same variable used multiple times is substituted everywhere."""
        template = "{{name}} is {{name}}'s name"
        context = {'name': 'John'}
        result = self.engine.render(template, context)
        assert result == "John is John's name"

    def test_complex_document(self):
        """Complex document with multiple features works correctly."""
        template = """
AGREEMENT

Parties: {{parties}}

{% if is_corporation %}
CORPORATE TERMS
This agreement is between {{company_name}} and its subsidiaries.
{% else %}
INDIVIDUAL TERMS
This agreement is between {{individual_name}}.
{% endif %}

Date: {{date}}
Value: ${{amount}}

{% if requires_witness %}
Witness: {{witness}}
{% endif %}
"""
        context = {
            'parties': ('Acme Corp', 'XYZ Inc'),
            'is_corporation': True,
            'company_name': 'Acme Corporation',
            'individual_name': None,
            'date': '2024-01-15',
            'amount': 50000,
            'requires_witness': False,
            'witness': None,
        }
        result = self.engine.render(template, context)

        assert "Acme Corp, XYZ Inc" in result
        assert "CORPORATE TERMS" in result
        assert "Acme Corporation" in result
        assert "INDIVIDUAL TERMS" not in result
        assert "2024-01-15" in result
        assert "$50000" in result
        assert "Witness:" not in result

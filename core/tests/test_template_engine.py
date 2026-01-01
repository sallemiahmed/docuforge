"""
Tests for DocuForge Template Engine

Tests the custom template syntax and type-safe variable handling.
"""
from django.test import TestCase
from core.parser import TemplateEngine


class TestVariableSubstitution(TestCase):
    """Tests for variable substitution."""

    def setUp(self):
        self.engine = TemplateEngine()

    def test_simple_variable(self):
        """Test simple variable substitution."""
        template = "Hello {{name}}!"
        context = {'name': 'John'}
        result = self.engine.render(template, context)
        self.assertEqual(result, "Hello John!")

    def test_multiple_variables(self):
        """Test multiple variables in template."""
        template = "{{greeting}} {{name}}, welcome to {{place}}!"
        context = {'greeting': 'Hello', 'name': 'John', 'place': 'DocuForge'}
        result = self.engine.render(template, context)
        self.assertEqual(result, "Hello John, welcome to DocuForge!")

    def test_none_value_becomes_empty_string(self):
        """Test that None values become empty strings."""
        template = "Value: {{value}}"
        context = {'value': None}
        result = self.engine.render(template, context)
        self.assertEqual(result, "Value:")

    def test_tuple_becomes_comma_separated(self):
        """Test that tuples become comma-separated strings."""
        template = "Items: {{items}}"
        context = {'items': ('Apple', 'Orange', 'Banana')}
        result = self.engine.render(template, context)
        self.assertEqual(result, "Items: Apple, Orange, Banana")

    def test_list_becomes_comma_separated(self):
        """Test that lists become comma-separated strings."""
        template = "Items: {{items}}"
        context = {'items': ['Apple', 'Orange', 'Banana']}
        result = self.engine.render(template, context)
        self.assertEqual(result, "Items: Apple, Orange, Banana")

    def test_boolean_true_becomes_yes(self):
        """Test that True becomes 'Yes'."""
        template = "Active: {{active}}"
        context = {'active': True}
        result = self.engine.render(template, context)
        self.assertEqual(result, "Active: Yes")

    def test_boolean_false_becomes_no(self):
        """Test that False becomes 'No'."""
        template = "Active: {{active}}"
        context = {'active': False}
        result = self.engine.render(template, context)
        self.assertEqual(result, "Active: No")

    def test_number_conversion(self):
        """Test number to string conversion."""
        template = "Age: {{age}}, Score: {{score}}"
        context = {'age': 25, 'score': 98.5}
        result = self.engine.render(template, context)
        self.assertEqual(result, "Age: 25, Score: 98.5")


class TestConditionals(TestCase):
    """Tests for conditional blocks."""

    def setUp(self):
        self.engine = TemplateEngine()

    def test_simple_if_true(self):
        """Test simple if block when condition is true."""
        template = "{% if show %}Visible{% endif %}"
        context = {'show': True}
        result = self.engine.render(template, context)
        self.assertEqual(result, "Visible")

    def test_simple_if_false(self):
        """Test simple if block when condition is false."""
        template = "{% if show %}Visible{% endif %}"
        context = {'show': False}
        result = self.engine.render(template, context)
        self.assertEqual(result, "")

    def test_if_else_true(self):
        """Test if/else when condition is true."""
        template = "{% if premium %}Premium{% else %}Free{% endif %}"
        context = {'premium': True}
        result = self.engine.render(template, context)
        self.assertEqual(result, "Premium")

    def test_if_else_false(self):
        """Test if/else when condition is false."""
        template = "{% if premium %}Premium{% else %}Free{% endif %}"
        context = {'premium': False}
        result = self.engine.render(template, context)
        self.assertEqual(result, "Free")

    def test_and_condition(self):
        """Test AND in condition."""
        template = "{% if age >= 18 AND consent %}OK{% endif %}"
        context = {'age': 21, 'consent': True}
        result = self.engine.render(template, context)
        self.assertEqual(result, "OK")

    def test_or_condition(self):
        """Test OR in condition."""
        template = "{% if admin OR mod %}Access{% endif %}"
        context = {'admin': False, 'mod': True}
        result = self.engine.render(template, context)
        self.assertEqual(result, "Access")


class TestValidation(TestCase):
    """Tests for template validation."""

    def setUp(self):
        self.engine = TemplateEngine()

    def test_valid_template(self):
        """Test validation of a valid template."""
        template = "Hello {{name}}"
        result = self.engine.validate(template)
        self.assertTrue(result['valid'])

    def test_get_variables(self):
        """Test extracting variables from template."""
        template = "{{a}} and {{b}} and {{c}}"
        variables = self.engine.get_variables(template)
        self.assertEqual(set(variables), {'a', 'b', 'c'})

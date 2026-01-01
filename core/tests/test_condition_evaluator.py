"""
Tests for DocuForge Condition Evaluator

Tests the boolean condition evaluation with correct operator precedence.
"""
from django.test import TestCase
from core.parser import ConditionEvaluator


class TestBasicConditions(TestCase):
    """Tests for basic condition evaluation."""

    def setUp(self):
        self.evaluator = ConditionEvaluator()

    def test_simple_true_variable(self):
        """Test simple true variable."""
        result = self.evaluator.evaluate("active", {'active': True})
        self.assertTrue(result)

    def test_simple_false_variable(self):
        """Test simple false variable."""
        result = self.evaluator.evaluate("active", {'active': False})
        self.assertFalse(result)

    def test_true_literal(self):
        """Test true literal."""
        result = self.evaluator.evaluate("true", {})
        self.assertTrue(result)

    def test_false_literal(self):
        """Test false literal."""
        result = self.evaluator.evaluate("false", {})
        self.assertFalse(result)


class TestComparisonOperators(TestCase):
    """Tests for comparison operators."""

    def setUp(self):
        self.evaluator = ConditionEvaluator()

    def test_equals(self):
        """Test == operator."""
        self.assertTrue(self.evaluator.evaluate("x == 5", {'x': 5}))
        self.assertFalse(self.evaluator.evaluate("x == 5", {'x': 3}))

    def test_not_equals(self):
        """Test != operator."""
        self.assertTrue(self.evaluator.evaluate("x != 5", {'x': 3}))
        self.assertFalse(self.evaluator.evaluate("x != 5", {'x': 5}))

    def test_less_than(self):
        """Test < operator."""
        self.assertTrue(self.evaluator.evaluate("x < 10", {'x': 5}))
        self.assertFalse(self.evaluator.evaluate("x < 10", {'x': 15}))

    def test_greater_than(self):
        """Test > operator."""
        self.assertTrue(self.evaluator.evaluate("x > 10", {'x': 15}))
        self.assertFalse(self.evaluator.evaluate("x > 10", {'x': 5}))

    def test_greater_than_or_equal(self):
        """Test >= operator."""
        self.assertTrue(self.evaluator.evaluate("x >= 10", {'x': 10}))
        self.assertFalse(self.evaluator.evaluate("x >= 10", {'x': 9}))


class TestBooleanOperators(TestCase):
    """Tests for boolean operators."""

    def setUp(self):
        self.evaluator = ConditionEvaluator()

    def test_simple_and(self):
        """Test AND operator."""
        self.assertTrue(self.evaluator.evaluate("a AND b", {'a': True, 'b': True}))
        self.assertFalse(self.evaluator.evaluate("a AND b", {'a': True, 'b': False}))

    def test_simple_or(self):
        """Test OR operator."""
        self.assertTrue(self.evaluator.evaluate("a OR b", {'a': True, 'b': False}))
        self.assertFalse(self.evaluator.evaluate("a OR b", {'a': False, 'b': False}))

    def test_not_operator(self):
        """Test NOT operator."""
        self.assertFalse(self.evaluator.evaluate("NOT a", {'a': True}))
        self.assertTrue(self.evaluator.evaluate("NOT a", {'a': False}))


class TestOperatorPrecedence(TestCase):
    """Tests for correct AND/OR precedence."""

    def setUp(self):
        self.evaluator = ConditionEvaluator()

    def test_and_before_or(self):
        """
        Test that AND is evaluated before OR.
        A AND B OR C = (A AND B) OR C
        """
        context = {'A': False, 'B': True, 'C': True}
        result = self.evaluator.evaluate("A AND B OR C", context)
        # (False AND True) OR True = False OR True = True
        self.assertTrue(result)

    def test_parentheses_override(self):
        """Test that parentheses override default precedence."""
        context = {'A': False, 'B': True, 'C': True}
        # A AND (B OR C) = False AND (True OR True) = False AND True = False
        result = self.evaluator.evaluate("A AND (B OR C)", context)
        self.assertFalse(result)

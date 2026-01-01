"""
Tests for DocuForge Condition Evaluator

CRITICAL: These tests verify correct AND/OR operator precedence.

The common bug is evaluating OR before AND, which produces incorrect results.
Standard precedence is: NOT > AND > OR

Example of the bug these tests catch:
    Condition: "A AND B OR C"

    WRONG (OR before AND): A AND (B OR C)
    RIGHT (AND before OR): (A AND B) OR C

    With A=False, B=True, C=True:
    WRONG: False AND (True OR True) = False AND True = False
    RIGHT: (False AND True) OR True = False OR True = True

Author: Ahmed Sallemi | MediaTree
"""
import pytest
from core.parser import ConditionEvaluator, ConditionEvaluationError


class TestBasicConditions:
    """Tests for basic condition evaluation."""

    def setup_method(self):
        self.evaluator = ConditionEvaluator()

    def test_simple_true_variable(self):
        """True variable evaluates to True."""
        result = self.evaluator.evaluate("is_active", {'is_active': True})
        assert result is True

    def test_simple_false_variable(self):
        """False variable evaluates to False."""
        result = self.evaluator.evaluate("is_active", {'is_active': False})
        assert result is False

    def test_missing_variable_is_falsy(self):
        """Missing variables evaluate to falsy (None -> False)."""
        result = self.evaluator.evaluate("nonexistent", {})
        assert result is False

    def test_empty_condition_is_true(self):
        """Empty condition evaluates to True."""
        result = self.evaluator.evaluate("", {})
        assert result is True


class TestComparisonOperators:
    """Tests for comparison operators."""

    def setup_method(self):
        self.evaluator = ConditionEvaluator()

    def test_equals_true(self):
        """Equality check returns True when equal."""
        result = self.evaluator.evaluate("status == 'active'", {'status': 'active'})
        assert result is True

    def test_equals_false(self):
        """Equality check returns False when not equal."""
        result = self.evaluator.evaluate("status == 'active'", {'status': 'inactive'})
        assert result is False

    def test_not_equals_true(self):
        """Not-equal check returns True when different."""
        result = self.evaluator.evaluate("status != 'deleted'", {'status': 'active'})
        assert result is True

    def test_greater_than(self):
        """Greater than comparison works."""
        result = self.evaluator.evaluate("age > 18", {'age': 25})
        assert result is True

    def test_greater_than_or_equal(self):
        """Greater than or equal comparison works."""
        result = self.evaluator.evaluate("age >= 18", {'age': 18})
        assert result is True

    def test_less_than(self):
        """Less than comparison works."""
        result = self.evaluator.evaluate("age < 18", {'age': 15})
        assert result is True

    def test_less_than_or_equal(self):
        """Less than or equal comparison works."""
        result = self.evaluator.evaluate("age <= 18", {'age': 18})
        assert result is True

    def test_numeric_comparison(self):
        """Numeric comparisons work correctly."""
        result = self.evaluator.evaluate("price > 100", {'price': 150})
        assert result is True


class TestBooleanOperators:
    """Tests for boolean operators (AND, OR, NOT)."""

    def setup_method(self):
        self.evaluator = ConditionEvaluator()

    def test_and_both_true(self):
        """AND returns True when both operands are True."""
        result = self.evaluator.evaluate("a AND b", {'a': True, 'b': True})
        assert result is True

    def test_and_one_false(self):
        """AND returns False when one operand is False."""
        result = self.evaluator.evaluate("a AND b", {'a': True, 'b': False})
        assert result is False

    def test_or_both_false(self):
        """OR returns False when both operands are False."""
        result = self.evaluator.evaluate("a OR b", {'a': False, 'b': False})
        assert result is False

    def test_or_one_true(self):
        """OR returns True when one operand is True."""
        result = self.evaluator.evaluate("a OR b", {'a': False, 'b': True})
        assert result is True

    def test_not_true(self):
        """NOT True returns False."""
        result = self.evaluator.evaluate("NOT a", {'a': True})
        assert result is False

    def test_not_false(self):
        """NOT False returns True."""
        result = self.evaluator.evaluate("NOT a", {'a': False})
        assert result is True


class TestOperatorPrecedence:
    """
    CRITICAL: Tests for correct AND/OR operator precedence.

    Standard precedence: NOT > AND > OR
    This means AND is evaluated before OR.

    "A AND B OR C" should be parsed as "(A AND B) OR C"
    NOT as "A AND (B OR C)"
    """

    def setup_method(self):
        self.evaluator = ConditionEvaluator()

    def test_and_before_or_basic(self):
        """
        AND should have higher precedence than OR.

        "a AND b OR c" = "(a AND b) OR c"

        With a=True, b=False, c=True:
        CORRECT: (True AND False) OR True = False OR True = True
        WRONG:   True AND (False OR True) = True AND True = True (same by coincidence)
        """
        result = self.evaluator.evaluate(
            "a AND b OR c",
            {'a': True, 'b': False, 'c': True}
        )
        assert result is True

    def test_and_before_or_reveals_bug(self):
        """
        This test REVEALS the precedence bug.

        "a AND b OR c" = "(a AND b) OR c"

        With a=False, b=True, c=True:
        CORRECT: (False AND True) OR True = False OR True = True
        WRONG:   False AND (True OR True) = False AND True = False
        """
        result = self.evaluator.evaluate(
            "a AND b OR c",
            {'a': False, 'b': True, 'c': True}
        )
        # CORRECT precedence gives True
        # WRONG precedence gives False
        assert result is True, "AND should have higher precedence than OR!"

    def test_multiple_and_or(self):
        """
        Multiple AND/OR operators maintain correct precedence.

        "a OR b AND c OR d" = "a OR (b AND c) OR d"
        """
        result = self.evaluator.evaluate(
            "a OR b AND c OR d",
            {'a': False, 'b': True, 'c': True, 'd': False}
        )
        # a OR (b AND c) OR d = False OR (True AND True) OR False = False OR True OR False = True
        assert result is True

    def test_and_or_with_comparisons(self):
        """
        Precedence works with comparison operators.

        "age > 65 AND has_insurance OR is_emergency"
        = "(age > 65 AND has_insurance) OR is_emergency"
        """
        # Case 1: Only emergency is true
        result = self.evaluator.evaluate(
            "age > 65 AND has_insurance OR is_emergency",
            {'age': 30, 'has_insurance': False, 'is_emergency': True}
        )
        assert result is True  # (False AND False) OR True = True

        # Case 2: Elderly with insurance, no emergency
        result = self.evaluator.evaluate(
            "age > 65 AND has_insurance OR is_emergency",
            {'age': 70, 'has_insurance': True, 'is_emergency': False}
        )
        assert result is True  # (True AND True) OR False = True

        # Case 3: None apply
        result = self.evaluator.evaluate(
            "age > 65 AND has_insurance OR is_emergency",
            {'age': 30, 'has_insurance': False, 'is_emergency': False}
        )
        assert result is False  # (False AND False) OR False = False

    def test_not_has_highest_precedence(self):
        """
        NOT should have highest precedence.

        "NOT a AND b" = "(NOT a) AND b"
        """
        result = self.evaluator.evaluate(
            "NOT a AND b",
            {'a': False, 'b': True}
        )
        # (NOT False) AND True = True AND True = True
        assert result is True

    def test_parentheses_override_precedence(self):
        """
        Parentheses should override default precedence.

        "a AND (b OR c)" - parentheses force OR to be evaluated first
        """
        result = self.evaluator.evaluate(
            "a AND (b OR c)",
            {'a': True, 'b': False, 'c': True}
        )
        # True AND (False OR True) = True AND True = True
        assert result is True

        # Compare without parentheses
        result = self.evaluator.evaluate(
            "a AND b OR c",
            {'a': True, 'b': False, 'c': True}
        )
        # (True AND False) OR True = False OR True = True
        assert result is True

    def test_complex_precedence_case(self):
        """
        Complex expression with correct precedence.

        "a OR b AND c OR d AND e"
        = "a OR (b AND c) OR (d AND e)"
        """
        result = self.evaluator.evaluate(
            "a OR b AND c OR d AND e",
            {'a': False, 'b': False, 'c': True, 'd': True, 'e': True}
        )
        # False OR (False AND True) OR (True AND True)
        # = False OR False OR True
        # = True
        assert result is True

    def test_real_world_clinical_example(self):
        """
        Real-world example: Clinical note generation logic.

        Include clause if:
        "is_diabetic AND age > 50 OR has_family_history"

        This should be: "(is_diabetic AND age > 50) OR has_family_history"
        """
        # Patient has family history but is young and not diabetic
        result = self.evaluator.evaluate(
            "is_diabetic AND age > 50 OR has_family_history",
            {'is_diabetic': False, 'age': 25, 'has_family_history': True}
        )
        assert result is True  # Should include clause due to family history

        # Patient is old diabetic without family history
        result = self.evaluator.evaluate(
            "is_diabetic AND age > 50 OR has_family_history",
            {'is_diabetic': True, 'age': 65, 'has_family_history': False}
        )
        assert result is True  # Should include clause due to age + diabetic

    def test_real_world_legal_example(self):
        """
        Real-world example: Legal document clause logic.

        Include liability clause if:
        "is_corporation AND has_board_approval OR is_emergency_filing"
        """
        # Emergency filing - should include regardless
        result = self.evaluator.evaluate(
            "is_corporation AND has_board_approval OR is_emergency_filing",
            {'is_corporation': False, 'has_board_approval': False, 'is_emergency_filing': True}
        )
        assert result is True

        # Corporation with board approval
        result = self.evaluator.evaluate(
            "is_corporation AND has_board_approval OR is_emergency_filing",
            {'is_corporation': True, 'has_board_approval': True, 'is_emergency_filing': False}
        )
        assert result is True

        # Corporation without board approval, not emergency
        result = self.evaluator.evaluate(
            "is_corporation AND has_board_approval OR is_emergency_filing",
            {'is_corporation': True, 'has_board_approval': False, 'is_emergency_filing': False}
        )
        assert result is False


class TestNestedContext:
    """Tests for nested variable access in conditions."""

    def setup_method(self):
        self.evaluator = ConditionEvaluator()

    def test_nested_variable_access(self):
        """Can access nested variables in conditions."""
        result = self.evaluator.evaluate(
            "user.role == 'admin'",
            {'user': {'role': 'admin'}}
        )
        assert result is True

    def test_deeply_nested_access(self):
        """Can access deeply nested variables."""
        result = self.evaluator.evaluate(
            "company.settings.allow_export == true",
            {'company': {'settings': {'allow_export': True}}}
        )
        assert result is True


class TestErrorHandling:
    """Tests for error handling."""

    def setup_method(self):
        self.evaluator = ConditionEvaluator()

    def test_invalid_operator_raises_error(self):
        """Invalid operators raise ConditionEvaluationError."""
        with pytest.raises(ConditionEvaluationError):
            self.evaluator.evaluate("a $$ b", {'a': True, 'b': True})

    def test_unbalanced_parentheses_raises_error(self):
        """Unbalanced parentheses raise error."""
        with pytest.raises(ConditionEvaluationError):
            self.evaluator.evaluate("(a AND b", {'a': True, 'b': True})

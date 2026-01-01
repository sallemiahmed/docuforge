"""
DocuForge Condition Evaluator

Evaluates boolean conditions with CORRECT operator precedence:
    NOT > AND > OR (standard boolean precedence)

This solves the common bug where AND/OR precedence is inverted,
causing conditions like "A AND B OR C" to evaluate incorrectly.

Supported syntax:
    - Comparisons: ==, !=, <, <=, >, >=
    - Boolean operators: AND, OR, NOT
    - Parentheses for explicit grouping
    - Variable references
    - Literal values: true, false, null, numbers, "strings"

Examples:
    "age >= 18 AND has_consent"
    "is_vip OR total_purchases > 1000"
    "status == 'active' AND (role == 'admin' OR role == 'manager')"

Author: Ahmed Sallemi | MediaTree
"""
import re
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum, auto

from .exceptions import ConditionEvaluationError


class TokenType(Enum):
    """Token types for the condition lexer."""
    VARIABLE = auto()
    NUMBER = auto()
    STRING = auto()
    BOOLEAN = auto()
    NULL = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    EQ = auto()      # ==
    NEQ = auto()     # !=
    LT = auto()      # <
    LTE = auto()     # <=
    GT = auto()      # >
    GTE = auto()     # >=
    LPAREN = auto()  # (
    RPAREN = auto()  # )
    EOF = auto()


@dataclass
class Token:
    """Represents a lexical token."""
    type: TokenType
    value: Any
    position: int = 0


class ConditionLexer:
    """Tokenizes condition strings."""

    KEYWORDS = {
        'and': TokenType.AND,
        'or': TokenType.OR,
        'not': TokenType.NOT,
        'true': TokenType.BOOLEAN,
        'false': TokenType.BOOLEAN,
        'null': TokenType.NULL,
        'none': TokenType.NULL,
    }

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.current_char = text[0] if text else None

    def advance(self):
        """Move to next character."""
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def skip_whitespace(self):
        """Skip whitespace characters."""
        while self.current_char and self.current_char.isspace():
            self.advance()

    def read_number(self) -> Token:
        """Read a numeric literal."""
        result = ''
        start_pos = self.pos
        has_dot = False

        while self.current_char and (self.current_char.isdigit() or self.current_char == '.'):
            if self.current_char == '.':
                if has_dot:
                    break
                has_dot = True
            result += self.current_char
            self.advance()

        value = float(result) if has_dot else int(result)
        return Token(TokenType.NUMBER, value, start_pos)

    def read_string(self, quote_char: str) -> Token:
        """Read a string literal."""
        start_pos = self.pos
        self.advance()  # Skip opening quote
        result = ''

        while self.current_char and self.current_char != quote_char:
            if self.current_char == '\\' and self.pos + 1 < len(self.text):
                self.advance()
                result += self.current_char
            else:
                result += self.current_char
            self.advance()

        self.advance()  # Skip closing quote
        return Token(TokenType.STRING, result, start_pos)

    def read_identifier(self) -> Token:
        """Read an identifier or keyword."""
        start_pos = self.pos
        result = ''

        while self.current_char and (self.current_char.isalnum() or self.current_char in '_.'):
            result += self.current_char
            self.advance()

        lower = result.lower()
        if lower in self.KEYWORDS:
            token_type = self.KEYWORDS[lower]
            if token_type == TokenType.BOOLEAN:
                return Token(token_type, lower == 'true', start_pos)
            return Token(token_type, result, start_pos)

        return Token(TokenType.VARIABLE, result, start_pos)

    def get_next_token(self) -> Token:
        """Get the next token from input."""
        while self.current_char:
            # Skip whitespace
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            # Numbers
            if self.current_char.isdigit():
                return self.read_number()

            # Strings
            if self.current_char in '"\'':
                return self.read_string(self.current_char)

            # Identifiers and keywords
            if self.current_char.isalpha() or self.current_char == '_':
                return self.read_identifier()

            # Two-character operators
            if self.pos + 1 < len(self.text):
                two_char = self.text[self.pos:self.pos + 2]
                if two_char == '==':
                    self.advance()
                    self.advance()
                    return Token(TokenType.EQ, '==', self.pos - 2)
                if two_char == '!=':
                    self.advance()
                    self.advance()
                    return Token(TokenType.NEQ, '!=', self.pos - 2)
                if two_char == '<=':
                    self.advance()
                    self.advance()
                    return Token(TokenType.LTE, '<=', self.pos - 2)
                if two_char == '>=':
                    self.advance()
                    self.advance()
                    return Token(TokenType.GTE, '>=', self.pos - 2)

            # Single-character operators
            pos = self.pos
            if self.current_char == '<':
                self.advance()
                return Token(TokenType.LT, '<', pos)
            if self.current_char == '>':
                self.advance()
                return Token(TokenType.GT, '>', pos)
            if self.current_char == '(':
                self.advance()
                return Token(TokenType.LPAREN, '(', pos)
            if self.current_char == ')':
                self.advance()
                return Token(TokenType.RPAREN, ')', pos)

            raise ConditionEvaluationError(
                self.text,
                f"Unexpected character '{self.current_char}' at position {self.pos}"
            )

        return Token(TokenType.EOF, None, self.pos)

    def tokenize(self) -> List[Token]:
        """Tokenize the entire input."""
        tokens = []
        while True:
            token = self.get_next_token()
            tokens.append(token)
            if token.type == TokenType.EOF:
                break
        return tokens


class ConditionEvaluator:
    """
    Evaluates boolean conditions with CORRECT operator precedence.

    Precedence (highest to lowest):
        1. Parentheses ()
        2. NOT
        3. Comparison operators (==, !=, <, <=, >, >=)
        4. AND
        5. OR

    This is the STANDARD boolean precedence that most programming languages use.
    A common bug is to evaluate OR before AND, which produces incorrect results.

    Example of the bug this class AVOIDS:
        Condition: "A AND B OR C"

        WRONG (OR before AND): A AND (B OR C)
        RIGHT (AND before OR): (A AND B) OR C

        With A=False, B=True, C=True:
        WRONG: False AND (True OR True) = False AND True = False
        RIGHT: (False AND True) OR True = False OR True = True
    """

    def __init__(self):
        self.tokens: List[Token] = []
        self.pos: int = 0
        self.current_token: Optional[Token] = None
        self.context: Dict[str, Any] = {}

    def evaluate(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        Evaluate a condition string against a context.

        Args:
            condition: The condition string to evaluate
            context: Dictionary of variable values

        Returns:
            Boolean result of the evaluation

        Raises:
            ConditionEvaluationError: If the condition is invalid
        """
        if not condition or not condition.strip():
            return True  # Empty condition is always true

        self.context = context
        lexer = ConditionLexer(condition.strip())
        self.tokens = lexer.tokenize()
        self.pos = 0
        self.current_token = self.tokens[0]

        try:
            result = self._parse_or()

            if self.current_token.type != TokenType.EOF:
                raise ConditionEvaluationError(
                    condition,
                    f"Unexpected token: {self.current_token.value}"
                )

            return bool(result)
        except Exception as e:
            if isinstance(e, ConditionEvaluationError):
                raise
            raise ConditionEvaluationError(condition, str(e))

    def _advance(self):
        """Move to the next token."""
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]

    def _parse_or(self) -> bool:
        """
        Parse OR expressions (lowest precedence).

        Grammar: or_expr = and_expr (OR and_expr)*
        """
        result = self._parse_and()

        while self.current_token.type == TokenType.OR:
            self._advance()
            right = self._parse_and()
            result = result or right

        return result

    def _parse_and(self) -> bool:
        """
        Parse AND expressions (higher precedence than OR).

        Grammar: and_expr = not_expr (AND not_expr)*
        """
        result = self._parse_not()

        while self.current_token.type == TokenType.AND:
            self._advance()
            right = self._parse_not()
            result = result and right

        return result

    def _parse_not(self) -> bool:
        """
        Parse NOT expressions (higher precedence than AND).

        Grammar: not_expr = NOT not_expr | comparison
        """
        if self.current_token.type == TokenType.NOT:
            self._advance()
            return not self._parse_not()

        return self._parse_comparison()

    def _parse_comparison(self) -> bool:
        """
        Parse comparison expressions.

        Grammar: comparison = primary (comp_op primary)?
        """
        left = self._parse_primary()

        if self.current_token.type in (
            TokenType.EQ, TokenType.NEQ,
            TokenType.LT, TokenType.LTE,
            TokenType.GT, TokenType.GTE
        ):
            op = self.current_token.type
            self._advance()
            right = self._parse_primary()

            if op == TokenType.EQ:
                return left == right
            elif op == TokenType.NEQ:
                return left != right
            elif op == TokenType.LT:
                return left < right
            elif op == TokenType.LTE:
                return left <= right
            elif op == TokenType.GT:
                return left > right
            elif op == TokenType.GTE:
                return left >= right

        # If no comparison, treat as boolean
        return bool(left)

    def _parse_primary(self) -> Any:
        """
        Parse primary expressions (highest precedence).

        Grammar: primary = LPAREN or_expr RPAREN | literal | variable
        """
        token = self.current_token

        if token.type == TokenType.LPAREN:
            self._advance()
            result = self._parse_or()
            if self.current_token.type != TokenType.RPAREN:
                raise ConditionEvaluationError(
                    "",
                    "Missing closing parenthesis"
                )
            self._advance()
            return result

        if token.type == TokenType.NUMBER:
            self._advance()
            return token.value

        if token.type == TokenType.STRING:
            self._advance()
            return token.value

        if token.type == TokenType.BOOLEAN:
            self._advance()
            return token.value

        if token.type == TokenType.NULL:
            self._advance()
            return None

        if token.type == TokenType.VARIABLE:
            self._advance()
            return self._resolve_variable(token.value)

        raise ConditionEvaluationError(
            "",
            f"Unexpected token: {token.value}"
        )

    def _resolve_variable(self, name: str) -> Any:
        """
        Resolve a variable name to its value from context.

        Supports dot notation for nested access: "user.profile.name"
        """
        parts = name.split('.')
        value = self.context

        for part in parts:
            if isinstance(value, dict):
                if part not in value:
                    return None  # Missing keys resolve to None
                value = value[part]
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None

        return value

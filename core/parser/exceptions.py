"""
Custom exceptions for the DocuForge template engine.

These provide clear, actionable error messages for debugging
template parsing and evaluation issues.
"""


class TemplateEngineError(Exception):
    """Base exception for all template engine errors."""
    pass


class VariableResolutionError(TemplateEngineError):
    """Raised when a variable cannot be resolved."""

    def __init__(self, variable_name: str, reason: str = None):
        self.variable_name = variable_name
        self.reason = reason
        message = f"Cannot resolve variable '{variable_name}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class ConditionEvaluationError(TemplateEngineError):
    """Raised when a condition cannot be evaluated."""

    def __init__(self, condition: str, reason: str = None):
        self.condition = condition
        self.reason = reason
        message = f"Cannot evaluate condition '{condition}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class CircularDependencyError(TemplateEngineError):
    """Raised when circular dependencies are detected in template references."""

    def __init__(self, dependency_chain: list):
        self.dependency_chain = dependency_chain
        chain_str = " -> ".join(dependency_chain)
        message = f"Circular dependency detected: {chain_str}"
        super().__init__(message)


class InvalidTemplateError(TemplateEngineError):
    """Raised when template syntax is invalid."""

    def __init__(self, template: str, reason: str = None):
        self.template = template[:100] + "..." if len(template) > 100 else template
        self.reason = reason
        message = f"Invalid template syntax"
        if reason:
            message += f": {reason}"
        super().__init__(message)

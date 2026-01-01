"""
DocuForge Variable Resolver

Resolves variable references from context dictionaries with:
- Dot notation support (user.profile.name)
- Safe nested access
- Clear error messages for missing variables

Author: Ahmed Sallemi | MediaTree
"""
from typing import Any, Dict, List, Optional

from .exceptions import VariableResolutionError


class VariableResolver:
    """
    Resolves variable names to values from a context dictionary.

    Supports:
    - Simple variables: "name" -> context['name']
    - Dot notation: "user.profile.name" -> context['user']['profile']['name']
    - Attribute access: "user.get_full_name" -> context['user'].get_full_name
    - Safe None handling: Returns None for missing keys instead of crashing

    Example:
        resolver = VariableResolver()
        context = {
            'user': {
                'name': 'John',
                'profile': {'age': 30}
            }
        }
        resolver.resolve('user.name', context)  # 'John'
        resolver.resolve('user.profile.age', context)  # 30
        resolver.resolve('user.missing', context)  # raises VariableResolutionError
    """

    def __init__(self, strict: bool = False):
        """
        Initialize the resolver.

        Args:
            strict: If True, raise error for missing variables.
                   If False, return None for missing variables.
        """
        self.strict = strict

    def resolve(self, name: str, context: Dict[str, Any]) -> Any:
        """
        Resolve a variable name to its value.

        Args:
            name: Variable name, optionally with dot notation
            context: Dictionary containing variable values

        Returns:
            The resolved value

        Raises:
            VariableResolutionError: If variable is missing and strict mode is on
        """
        if not name:
            raise VariableResolutionError("", "Empty variable name")

        parts = name.split('.')
        value = context
        resolved_path = []

        for part in parts:
            resolved_path.append(part)

            if value is None:
                if self.strict:
                    raise VariableResolutionError(
                        name,
                        f"Cannot access '{part}' on None value at '{'.'.join(resolved_path[:-1])}'"
                    )
                return None

            if isinstance(value, dict):
                if part in value:
                    value = value[part]
                elif self.strict:
                    raise VariableResolutionError(
                        name,
                        f"Key '{part}' not found in dict at '{'.'.join(resolved_path[:-1]) or 'root'}'"
                    )
                else:
                    return None

            elif hasattr(value, part):
                attr = getattr(value, part)
                # If it's a method with no required args, call it
                if callable(attr):
                    try:
                        value = attr()
                    except TypeError:
                        # Method requires arguments, return the method itself
                        value = attr
                else:
                    value = attr

            elif self.strict:
                raise VariableResolutionError(
                    name,
                    f"Attribute '{part}' not found on {type(value).__name__}"
                )
            else:
                return None

        return value

    def resolve_all(self, names: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve multiple variable names.

        Args:
            names: List of variable names
            context: Context dictionary

        Returns:
            Dict mapping variable names to their resolved values
        """
        return {name: self.resolve(name, context) for name in names}

    def has_variable(self, name: str, context: Dict[str, Any]) -> bool:
        """Check if a variable exists in the context."""
        try:
            value = self.resolve(name, context)
            return value is not None
        except VariableResolutionError:
            return False

    def get_available_variables(self, context: Dict[str, Any], prefix: str = '') -> List[str]:
        """
        Get all available variable names from a context.

        Recursively explores nested dicts to find all possible variable paths.

        Args:
            context: Context dictionary
            prefix: Current path prefix (for recursion)

        Returns:
            List of all available variable paths
        """
        variables = []

        for key, value in context.items():
            full_path = f"{prefix}.{key}" if prefix else key
            variables.append(full_path)

            # Recurse into nested dicts
            if isinstance(value, dict):
                variables.extend(self.get_available_variables(value, full_path))

        return variables

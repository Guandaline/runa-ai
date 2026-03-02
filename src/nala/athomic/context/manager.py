# nala/athomic/context/manager.py

from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from nala.athomic.observability import get_logger

logger = get_logger(__name__)


@dataclass
class ContextVarInfo:
    """A data class that stores a ContextVar and its associated metadata.

    Attributes:
        var (ContextVar): The actual `ContextVar` instance.
        propagate (bool): If True, this variable's value should be propagated
            to background tasks and events.
        default (Any): The default value for the context variable.
    """

    var: ContextVar
    propagate: bool = False
    default: Any = None


class ContextVarManager:
    """Manages the registration and access for all application ContextVars.

    This class acts as a centralized registry for `contextvars`, making them
    discoverable and manageable. It abstracts the direct handling of `ContextVar`
    objects and provides a consistent API for setting, getting, and resetting
    context. It also plays a key role in context propagation by tracking which
    variables should be passed to background tasks.

    Attributes:
        _vars (Dict[str, ContextVarInfo]): The internal dictionary storing
            the registered ContextVarInfo objects.
    """

    def __init__(self) -> None:
        """Initializes the ContextVarManager."""
        self._vars: Dict[str, ContextVarInfo] = {}

    def register(
        self, name: str, propagate: bool = False, default: Optional[Any] = None
    ) -> None:
        """Registers a new ContextVar with the manager.

        Args:
            name (str): The unique name for the context variable.
            propagate (bool): If True, marks the variable for propagation to
                background tasks.
            default (Optional[Any]): The default value for the variable.
        """
        if name in self._vars:
            logger.warning(f"Context variable '{name}' is being overwritten.")

        logger.debug(f"Registering context variable '{name}' with default '{default}'")

        self._vars[name] = ContextVarInfo(
            var=ContextVar(name, default=default), propagate=propagate, default=default
        )

        logger.trace(f"Context variable '{name}' registered (propagate={propagate}).")

    def get(self, name: str, default: Optional[Any] = None) -> Any:
        """Gets the current value of a registered ContextVar.

        Args:
            name (str): The name of the variable to retrieve.
            default (Optional[Any]): A fallback value if the variable is not set.

        Returns:
            Any: The value of the context variable.
        """
        info = self._vars.get(name)
        return info.var.get(default) if info else default

    def set(self, name: str, value: Any) -> Optional[Token]:
        """Sets the value of a registered ContextVar.

        Args:
            name (str): The name of the variable to set.
            value (Any): The new value for the variable.

        Returns:
            Optional[Token]: The token to be used with `reset()`, or None if the
            variable is not registered.
        """
        info = self._vars.get(name)

        if info:
            return info.var.set(value)

        logger.warning(f"Attempted to set unregistered context variable '{name}'.")
        return None

    def reset(self, name: str, token: Token) -> None:
        """Resets a ContextVar to its previous value using its token.

        Args:
            name (str): The name of the variable to reset.
            token (Token): The token returned by the corresponding `set` call.
        """
        info = self._vars.get(name)

        if info:
            info.var.reset(token)

    def get_propagated_vars(self) -> Dict[str, ContextVarInfo]:
        """Returns a dictionary of all variables marked for propagation.

        Returns:
            Dict[str, ContextVarInfo]: A dictionary of variables where the
            `propagate` flag is True.
        """
        return {name: info for name, info in self._vars.items() if info.propagate}

    def get_all_vars(self) -> Dict[str, ContextVarInfo]:
        """Returns all registered ContextVarInfo objects.

        Returns:
            Dict[str, ContextVarInfo]: A dictionary of all registered variables.
        """
        return self._vars

    def register_from_definitions(
        self, var_definitions: List[Tuple[str, Any]], vars_to_propagate: List[str]
    ) -> None:
        """Registers multiple context variables from a list of definitions.

        Args:
            var_definitions (List[Tuple[str, Any]]): A list of tuples, where
                each tuple is `(name, default_value)`.
            vars_to_propagate (List[str]): A list of variable names from the
                definitions that should be marked for propagation.
        """
        logger.debug("Registering context variables from definitions.")
        for name, default_value in var_definitions:
            self.register(
                name=name, propagate=(name in vars_to_propagate), default=default_value
            )

    def get_current_context_dict(self) -> Dict[str, Any]:
        """Returns a dictionary snapshot of the current state of all context variables.

        Returns:
            Dict[str, Any]: A dictionary mapping variable names to their current values.
        """
        all_vars = context_var_manager.get_all_vars()
        return {name: info.var.get() for name, info in all_vars.items()}

    def clear_all_context(self) -> None:
        """Resets all registered context variables to their default values.

        This is primarily useful for ensuring a clean state in tests.
        """
        logger.debug("Clearing all context variables to their default values.")
        all_vars = context_var_manager.get_all_vars()

        for name, info in all_vars.items():
            logger.debug(f"Resetting context variable '{name}' to default.")
            info.var.set(info.default)
            logger.trace(
                f"Context variable '{name}' reset to default value '{info.default}'."
            )


# Singleton instance
context_var_manager = ContextVarManager()

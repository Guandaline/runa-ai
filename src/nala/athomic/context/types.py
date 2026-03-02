# nala/athomic/context/types.py
from typing import Callable, List, Union

# This type represents the flexible ways a developer can define how a
# context-aware key should be generated from a function's arguments.
ContextualKeyResolverType = Union[Callable[..., Union[str, List[str]]], str, List[str]]

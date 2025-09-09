import json
from typing import Callable, Dict, List, Optional

TYPE_MAPPING = {  # limited types supported :p
    "int": int,
    "str": str,
    "bool": bool,
    "float": float,
}


def get_signature(fn: Callable) -> dict:
    """Generates the signature for a given function."""
    schema = {
        "name": fn.__name__,
        "description": fn.__doc__,
        "arguments": {
            k: {"type": v.__name__}
            for k, v in fn.__annotations__.items() if k != "return"
        },
    }
    return schema


def validate_args(args: dict, args_schema: dict) -> dict:
    """Returns args dict with values converted to correct type.
    Example usage:
    >>> args = {'latitude': '14.4833', 'longitude': '121.2667'}
    >>> args_schema = {'latitude': {'type': 'float'}, 'longitude': {'type': 'float'}}
    >>> validate_args(args, args_schema)
    {'latitude': 14.4833, 'longitude': 121.2667}
    """

    # loop thru tool typed arguments, i.e. untyped = skip
    for arg, value in args.items():
        t = TYPE_MAPPING[args_schema.get(arg)["type"]]
        if not isinstance(value, t):
            args[arg] = t(value)
    return args


class Tool:
    """
    A class representing a tool that wraps a callable and its signature.
    Attributes:
        name (str): The name of the tool (function).
        fn (Callable): The function that the tool represents.
        signature (str): JSON string representation of the function's signature.
    """

    # Class-level registry instead of global variables
    _registry: Dict[str, "Tool"] = {}

    def __init__(self, name: str, fn: Callable, signature: str):
        self.name = name
        self.fn = fn
        self.signature = signature
        self.__class__._registry[name] = self

    def __str__(self):
        return json.dumps(self.signature)

    def __call__(self, **kwargs):
        tool_call = {"name": self.name, "arguments": kwargs, "id": -1}
        kwargs = Tool.validate_tool_call(tool_call)
        return self.fn(**kwargs)

    @classmethod
    def validate_tool_call(cls, tool_call: dict):
        required_keys = ["name", "arguments", "id"]
        assert set(required_keys) == set(tool_call.keys()), "missing tool call field"
        assert isinstance(tool_call["id"], int)
        args = tool_call["arguments"]
        name = tool_call["name"]
        schema = Tool.get_tool(name).signature["arguments"]
        return validate_args(args=args, args_schema=schema)

    @classmethod
    def execute(cls, tool_call: str | dict):
        """Execute the function from natural language."""
        tool_call = json.loads(tool_call) if isinstance(tool_call, str) else tool_call
        name = tool_call["name"]
        args = tool_call["arguments"]
        return Tool.get_tool(name)(**args)

    @classmethod
    def get_tool(cls, name: str) -> Optional["Tool"]:
        """Get a tool by name from the registry."""
        return cls._registry.get(name)

    @classmethod
    def get_all_tools(cls) -> List[dict]:
        """Get signatures of all registered tools."""
        return [tool.signature for tool in cls._registry.values()]

    @classmethod
    def clear_registry(cls):
        """Clear the tool registry (mainly for testing)."""
        cls._registry.clear()


def tool(fn: Callable):
    """Convert function to a tool (e.g. use as decorator)."""
    if isinstance(fn, Tool):
        return fn
    return Tool(fn.__name__, fn, get_signature(fn))

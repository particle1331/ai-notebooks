import inspect
import json
from typing import Callable, Dict, List, Optional


def get_signature(fn: Callable) -> dict:
    """Generates the signature for a given function."""

    # get required params and types from fn signature
    required = []
    properties = {}
    for v in inspect.signature(fn).parameters.values():
        properties[v.name] = {"type": str(v.annotation)}
        if v.default == inspect._empty:
            required.append(v.name)
        else:
            properties[v.name]["default"] = v.default

    return {
        "type": "function",
        "function": {
            "name": fn.__name__,
            "description": fn.__doc__,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
            "strict": True,
        },
    }


def validate_args(args: dict, args_schema: dict) -> dict:
    """Returns args dict with values converted to correct type.
    Example usage:
    >>> args = {'latitude': '14.4833', 'longitude': '121.2667'}
    >>> args_schema = {'latitude': {'type': '<class 'float'>'}, 'longitude': {'type': '<class 'float'>'}}
    >>> validate_args(args, args_schema)
    {'latitude': 14.4833, 'longitude': 121.2667}
    """

    type_mapping = {  # limited types supported :p
        "<class 'int'>": int,
        "<class 'str'>": str,
        "<class 'bool'>": bool,
        "<class 'float'>": float,
    }

    # loop thru tool typed arguments, i.e. untyped = skip
    for arg, value in args.items():
        t = type_mapping[args_schema.get(arg)["type"]]
        if not isinstance(value, t):
            args[arg] = t(value)
    return args


class Tool:
    """
    A class representing a tool that wraps a callable and its signature.
    Attributes:
        name (str): The name of the tool (function).
        fn (Callable): The function that the tool represents.
    """

    # Class-level registry instead of global variables
    _registry: Dict[str, "Tool"] = {}

    def __init__(self, fn: Callable):
        self.fn = fn
        self.name = fn.__name__
        self.signature = get_signature(fn)
        self.__class__._registry[self.name] = self

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
        schema = Tool.get_tool(name).signature["function"]["parameters"]["properties"]
        return validate_args(args=args, args_schema=schema)

    @classmethod
    def execute(cls, tool_call: str | dict):
        """Execute the function from natural language."""
        tool_call = json.loads(tool_call) if isinstance(tool_call, str) else tool_call
        name = tool_call["name"]
        args = tool_call["parameters"]
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

    @property
    def __name__(self):
        return self.name


def tool(fn: Callable):
    """Convert function to a tool (e.g. use as decorator)."""
    return fn if isinstance(fn, Tool) else Tool(fn)

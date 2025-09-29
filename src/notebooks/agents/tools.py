import inspect
import json
from typing import Callable, Dict, List, Optional


def get_signature(fn: Callable) -> dict:
    """Generates the signature for a given function."""

    json_types = {  # limited types supported :p
        "int": "integer",
        "str": "string",
        "bool": "boolean",
        "float": "number",
    }

    # get required params and types from fn signature
    required = []
    properties = {}
    for v in inspect.signature(fn).parameters.values():
        properties[v.name] = {"type": json_types[v.annotation.__name__]}
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
    >>> args_schema = {'latitude': {'type': 'number'}, 'longitude': {'type': 'number'}}
    >>> validate_args(args, args_schema)
    {'latitude': 14.4833, 'longitude': 121.2667}
    """

    type_mapping = {  # limited types supported :p
        "integer": int,
        "string": str,
        "boolean": bool,
        "number": float,
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

    def __str__(self) -> str:
        return json.dumps(self.signature)

    def __call__(self, **kwargs):
        return self.fn(**kwargs)
    
    @classmethod
    def parse_tool_call(cls, tool_call: str | dict):
        if isinstance(tool_call, str):
            tool_call = json.loads(tool_call)

        assert set(["function", "id"]) <= set(tool_call.keys())
        assert tool_call["id"].isnumeric()
        assert str(int(tool_call["id"])) == tool_call["id"]
        assert set(tool_call["function"].keys()) == set(["arguments", "name"])
        
        name = tool_call["function"]["name"]
        schema = Tool.get_tool(name).signature["function"]["parameters"]["properties"]
        args = json.loads(tool_call["function"]["arguments"])
        args = validate_args(args=args, args_schema=schema)  
        return name, args

    @classmethod
    def execute(cls, tool_call: str | dict):
        """Execute a tool call from text or schema."""
        name, args = cls.parse_tool_call(tool_call)
        return Tool.get_tool(name)(**args)

    @classmethod
    def get_tool(cls, name: str) -> Optional["Tool"]:
        """Get a tool by name from the registry."""
        return cls._registry[name]

    @classmethod
    def list_tools(cls) -> List[dict]:
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

"""Small, labeled display correction grounded in the submitted AST and example."""

import ast

from .schema import Diagnosis


def checked_prose(code: str, failure: str, answer: Diagnosis):
    try:
        program = ast.parse(code).body
        example = ast.parse(failure.splitlines()[0], mode="eval").body
    except (ValueError, SyntaxError, IndexError, RecursionError):
        return answer, None
    if len(program) != 1 or not isinstance(program[0], ast.FunctionDef):
        return answer, None
    fn = program[0]
    if (
        fn.decorator_list
        or fn.name == "bool"
        or len(fn.args.args) != 1
        or fn.args.posonlyargs
        or fn.args.kwonlyargs
        or fn.args.vararg
        or fn.args.kwarg
        or fn.args.args[0].arg == "bool"
        or len(fn.body) != 1
        or not isinstance(fn.body[0], ast.Return)
    ):
        return answer, None
    if not (
        isinstance(example, ast.Call)
        and isinstance(example.func, ast.Name)
        and example.func.id == fn.name
        and len(example.args) == 1
        and not example.keywords
        and isinstance(example.args[0], ast.Constant)
        and isinstance(example.args[0].value, str)
    ):
        return answer, None
    expr = fn.body[0].value
    if not (
        isinstance(expr, ast.Call)
        and isinstance(expr.func, ast.Name)
        and expr.func.id == "bool"
        and not expr.keywords
        and len(expr.args) == 1
        and isinstance(expr.args[0], ast.Attribute)
    ):
        return answer, None
    attr = expr.args[0]
    if not (
        isinstance(attr.value, ast.Name)
        and attr.value.id == fn.args.args[0].arg
        and attr.attr in {"strip", "lstrip", "rstrip"}
    ):
        return answer, None
    name = f"{attr.value.id}.{attr.attr}"
    checked = answer.model_copy(
        update={
            "root_cause": f"{name} is a bound method. Testing that object yields True even when the string contains only whitespace.",
            "explanation": f"Call {name}() before converting its result to bool. In the supplied example the receiver is a string. An empty result is false, and a nonempty result is true.",
        }
    )
    return checked, "Python semantics check"

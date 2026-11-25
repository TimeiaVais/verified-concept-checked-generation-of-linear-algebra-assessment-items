"""Check generated family code before it runs.

The check reads the code with `ast` and runs none of it. It rejects imports outside an allowlist,
calls that reach files, the network or the interpreter, a missing family class, and mathematics in
`solve` that does not go through the step library, since a step that bypasses the library leaves
its concept out of the trace.
"""

import ast
import typing

from la_items import contracts

__all__ = ["ALLOWED_MODULES", "find_family_class", "find_static_failure"]

ALLOWED_MODULES: typing.Final = frozenset(
    {
        "random",
        "typing",
        "collections",
        "collections.abc",
        "sympy",
        "la_items.contracts",
        "la_items.steplib.determinants",
        "la_items.steplib.linear_systems",
        "la_items.steplib.eigenvalues",
    }
)
_STEP_MODULES: typing.Final = frozenset(
    name for name in ALLOWED_MODULES if name.startswith("la_items.steplib.")
)
_FORBIDDEN_NAMES: typing.Final = frozenset(
    {
        "open",
        "exec",
        "eval",
        "compile",
        "__import__",
        "globals",
        "locals",
        "vars",
        "getattr",
        "setattr",
        "delattr",
        "input",
        "breakpoint",
        "memoryview",
    }
)
_FAMILY_METHODS: typing.Final = frozenset(
    {
        "sample_parameters",
        "find_parameter_problem",
        "render_question",
        "solve",
        "compute_reference_answer",
    }
)
_FAMILY_ATTRIBUTES: typing.Final = frozenset({"name", "target_concepts", "parameter_shapes"})


def _fail(reason: contracts.Reason, detail: str) -> contracts.CheckFailure:
    failure = contracts.CheckFailure("static_check", reason, detail)

    return failure


def find_family_class(tree: ast.Module) -> ast.ClassDef | None:
    """Return the first top-level class with every attribute and method of `ItemFamily`.

    Parameters
    ----------
    tree : ast.Module
        The parsed module.

    Returns
    -------
    ast.ClassDef | None
        The family class, or None.
    """
    candidates = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            methods = {item.name for item in node.body if isinstance(item, ast.FunctionDef)}
            attributes = {
                target.id
                for item in node.body
                if isinstance(item, ast.Assign | ast.AnnAssign)
                for target in (item.targets if isinstance(item, ast.Assign) else [item.target])
                if isinstance(target, ast.Name)
            }
            if _FAMILY_METHODS <= methods and _FAMILY_ATTRIBUTES <= attributes:
                candidates.append(node)

    family_class = candidates[0] if candidates else None

    return family_class


def _list_imports(tree: ast.Module) -> list[tuple[str, bool, str, str | None]]:
    """Each imported name as (statement, is_allowed, bound name, "module", "function" or None)."""
    imports: list[tuple[str, bool, str, str | None]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports += [
                (
                    f"import {alias.name}",
                    alias.name in ALLOWED_MODULES,
                    alias.asname or alias.name,
                    "module" if alias.name in _STEP_MODULES else None,
                )
                for alias in node.names
            ]

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports += [
                (
                    f"from {'.' * node.level}{module} import {alias.name}",
                    not node.level
                    and (module in ALLOWED_MODULES or f"{module}.{alias.name}" in ALLOWED_MODULES),
                    alias.asname or alias.name,
                    (
                        "module"
                        if f"{module}.{alias.name}" in _STEP_MODULES
                        else ("function" if module in _STEP_MODULES else None)
                    ),
                )
                for alias in node.names
            ]

    return imports


def _find_import_failure(
    tree: ast.Module,
) -> tuple[contracts.CheckFailure | None, set[str], set[str]]:
    """Check every import; return the names bound to step modules and to step functions."""
    imports = _list_imports(tree)
    forbidden = [statement for statement, is_allowed, _, _ in imports if not is_allowed]
    failure = _fail("forbidden_import", forbidden[0]) if forbidden else None
    step_modules = {
        bound for _, is_allowed, bound, kind in imports if is_allowed and kind == "module"
    }
    step_functions = {
        bound for _, is_allowed, bound, kind in imports if is_allowed and kind == "function"
    }
    checked_imports = failure, step_modules, step_functions

    return checked_imports


def _find_call_failure(tree: ast.Module) -> contracts.CheckFailure | None:
    failure = None

    for node in ast.walk(tree):
        if failure is None and isinstance(node, ast.Name) and node.id in _FORBIDDEN_NAMES:
            failure = _fail("forbidden_call", f"use of {node.id} on line {node.lineno}")

        elif failure is None and isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            failure = _fail("forbidden_call", f"use of .{node.attr} on line {node.lineno}")

    return failure


def _find_solve_failure(
    family_class: ast.ClassDef, step_modules: set[str], step_functions: set[str]
) -> contracts.CheckFailure | None:
    solve = next(
        item
        for item in family_class.body
        if isinstance(item, ast.FunctionDef) and item.name == "solve"
    )
    failure = None

    for node in ast.walk(solve):
        is_arithmetic = isinstance(node, ast.BinOp | ast.AugAssign) or (
            isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub | ast.UAdd)
        )
        is_step_call = isinstance(node, ast.Call) and (
            (isinstance(node.func, ast.Name) and node.func.id in step_functions)
            or (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in step_modules
            )
        )

        if failure is None and is_arithmetic:
            failure = _fail(
                "math_outside_step_library",
                f"solve uses an arithmetic operator on line {node.lineno}",  # type: ignore[attr-defined]
            )

        elif failure is None and isinstance(node, ast.Call) and not is_step_call:
            failure = _fail(
                "math_outside_step_library",
                f"solve calls {ast.unparse(node.func)} on line {node.lineno}, "
                "which is not a step library function",
            )

    return failure


def find_static_failure(source: str) -> contracts.CheckFailure | None:
    """Return the first rule the generated code breaks, or None.

    Parameters
    ----------
    source : str
        The generated module.

    Returns
    -------
    contracts.CheckFailure | None
        A failure of the "static_check" stage, or None when the code may run.
    """
    try:
        tree = ast.parse(source)
        import_failure, step_modules, step_functions = _find_import_failure(tree)
        family_class = find_family_class(tree)

        if import_failure is not None:
            failure: contracts.CheckFailure | None = import_failure

        elif (call_failure := _find_call_failure(tree)) is not None:
            failure = call_failure

        elif family_class is None:
            failure = _fail(
                "missing_family",
                "no class with name, target_concepts, parameter_shapes and the five ItemFamily "
                "methods",
            )

        else:
            failure = _find_solve_failure(family_class, step_modules, step_functions)

    except SyntaxError as error:
        failure = _fail("syntax_error", f"{error.msg} on line {error.lineno}")

    return failure

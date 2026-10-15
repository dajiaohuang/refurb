from dataclasses import dataclass

from mypy.nodes import ArgKind, CallExpr, NameExpr

from refurb.checks.common import stringify
from refurb.checks.pathlib.util import is_pathlike
from refurb.error import Error


@dataclass
class ErrorInfo(Error):
    """
    When you want to open a Path object, don't pass it to `open()`, just call
    `.open()` on the Path object itself:

    Bad:

    ```
    path = Path("filename")

    with open(path) as f:
        pass
    ```

    Good:

    ```
    path = Path("filename")

    with path.open() as f:
        pass
    ```
    """

    name = "use-pathlib-open"
    code = 117
    categories = ("pathlib",)


def check(node: CallExpr, errors: list[Error]) -> None:
    match node:
        case CallExpr(
            callee=NameExpr(fullname="builtins.open") as open_node,
            args=[
                CallExpr(
                    callee=NameExpr(fullname="builtins.str"),
                    args=[arg],
                )
                | arg,
                *rest,
            ],
        ) if is_pathlike(arg):
            if node.arg_kinds[1:].count(ArgKind.ARG_POS) > 5:
                return

            args: list[str] = []

            for value, kind, name in zip(rest, node.arg_kinds[1:], node.arg_names[1:]):
                if kind == ArgKind.ARG_POS:
                    args.append(stringify(value))

                elif kind == ArgKind.ARG_NAMED and name in (
                    "mode",
                    "buffering",
                    "encoding",
                    "errors",
                    "newline",
                ):
                    args.append(f"{name}={stringify(value)}")

                else:
                    return

            inner = stringify(arg)
            old = stringify(node)
            new = f"{inner}.open({', '.join(args)})"

            msg = f"Replace `{old}` with `{new}`"

            errors.append(ErrorInfo.from_node(open_node, msg))

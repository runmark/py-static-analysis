from model import AnalysisContext
import ast


class LineLengthVisitor(ast.NodeVisitor):
    max_length = 79
    docstring_max_length = 72

    def __init__(self, ctx: AnalysisContext):
        super().__init__()
        self.ctx = ctx

    def visit(self, node: ast.AST):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef, ast.ClassDef)):
            self.check_docstring(node)

        if (
            "end_col_offset" in node._attributes
            and node.end_col_offset >= self.max_length
        ):
            self.ctx.add_issue(
                node, "W0001", f"Exceed max line length({self.max_length})"
            )
        else:
            # exit current ast node, visit next node
            self.generic_visit(node)

    def check_docstring(self, node: ast.AST):
        docstring_node = self.get_docstring_node(node)
        if not docstring_node:
            return self.generic_visit(node)

        for offset, line in enumerate(docstring_node.value.split("\n")):
            if len(line) > self.docstring_max_length:
                lineno = docstring_node.lineno + offset
                self.ctx.add_issue(
                    node,
                    "W0001",
                    f"Docstring for {node.name} exceed max length({self.docstring_max_length})",
                    lineno=lineno,
                )

    def get_docstring_node(self, node: ast.AST):
        if not isinstance(
            node, (ast.AsyncFunctionDef, ast.FunctionDef, ast.ClassDef, ast.Module)
        ):
            raise TypeError("%r can't have docstrings" % node.__class__.__name__)

        if not (node.body and isinstance(node.body[0], ast.Expr)):
            return None

        node = node.body[0].value
        if isinstance(node, ast.Str):
            return node
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node
        else:
            return None

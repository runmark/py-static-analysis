from model import AnalysisContext
import ast


class LineLengthVisitor(ast.NodeVisitor):
    max_length = 79

    def __init__(self, ctx: AnalysisContext):
        super().__init__()
        self.ctx = ctx

    def visit(self, node: ast.AST):
        if (
            "end_col_offset" in node._attributes
            and node.end_col_offset >= self.max_length
        ):
            self.ctx.add_issue(
                node, "W0001", f"Exceed max line length({self.max_length})"
            )
        else:
            self.generic_visit(node)

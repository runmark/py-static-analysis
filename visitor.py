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


class ExceptionTypeVisitor(ast.NodeVisitor):
    avoid_type = (Exception, BaseException)

    def __init__(self, ctx: AnalysisContext):
        super().__init__()
        self.ctx = ctx

    def visit_ExceptHandler(self, node: ast.AST):
        if not node.type:
            self.ctx.add_issue(
                node, "W0002", f"Please specify exception type to catch."
            )

        for except_type in self.iter_except_type(node.type):
            if isinstance(except_type, ast.Name) and except_type.id == "Exception":
                self.ctx.add_issue(node, "W0002", f"Avoid catch generic Exception.")
        self.generic_visit(node)

    def iter_except_type(self, node: ast.AST):
        if isinstance(node, ast.Name):
            yield node
        elif isinstance(node, ast.Tuple):
            for elt in node.elts:
                if isinstance(elt, ast.Name):
                    yield elt


class VariableScope:
    def __init__(self, node: ast.FunctionDef):
        self.node = node
        self.declare_vars = {}
        self.used_vars = set()

    def use(self, node: ast.Name, in_assign: bool):
        var_name = node.id
        if in_assign and isinstance(node.ctx, ast.Store):
            self.declare_vars[var_name] = node
        else:
            self.used_vars.add(var_name)

    def check(self, ctx: AnalysisContext):
        unused_vars = set(self.declare_vars) - self.used_vars
        for unused_var in unused_vars:
            ctx.add_issue(
                self.declare_vars[unused_var],
                "W0003",
                f"Variable '{unused_var}' declared but never used",
            )


class VariableUsageVisitor(ast.NodeVisitor):
    def __init__(self, ctx: AnalysisContext):
        super().__init__()
        self.ctx = ctx
        self.in_assign = False
        self.scope_stack = []
        # self.assigned_vars = {}
        # self.used_vars = set()

    def visit(self, node: ast.AST):
        is_scope_ast = isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef))
        if is_scope_ast:
            scope = VariableScope(node)
            self.scope_stack.append(scope)
        # self.generic_visit(node)
        super().visit(node)
        if is_scope_ast:
            self.scope_stack.remove(scope)
            scope.check(self.ctx)

    def visit_Assign(self, node: ast.Assign):
        self.in_assign = True
        self.generic_visit(node)
        self.in_assign = False

    def visit_Name(self, node: ast.Name):
        if self.scope_stack:
            scope = self.scope_stack[-1]
            scope.use(node, self.in_assign)
        self.generic_visit(node)


class PreferIsNotVisitor(ast.NodeVisitor):
    def __init__(self, ctx: AnalysisContext):
        super().__init__()
        self.ctx = ctx

    def visit_If(self, node: ast.If):
        if isinstance(node.test, ast.UnaryOp) and isinstance(node.test.op, ast.Not):
            operand = node.test.operand
            if (
                isinstance(operand, ast.Compare)
                and len(operand.ops) == 1
                and isinstance(operand.ops[0], ast.Is)
            ):
                self.ctx.add_issue(node, "W0004", "Use if ... is not instead")
        self.generic_visit(node)


class CodeAnalyzer:
    def visitors(self, ctx: AnalysisContext):
        yield LineLengthVisitor(ctx)
        yield ExceptionTypeVisitor(ctx)
        yield VariableUsageVisitor(ctx)
        yield PreferIsNotVisitor(ctx)

    def analysis(self, filename: str, code: str):
        self.ctx = AnalysisContext(filename)
        ast_root = ast.parse(code)
        for visitor in self.visitors(self.ctx):
            visitor.visit(ast_root)

    def print(self):
        for issue in self.ctx.issues:
            print(issue)


if __name__ == "__main__":
    analyzer = CodeAnalyzer()
    analyzer.analysis("test.py", CODE)
    analyzer.print()

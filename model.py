from dataclasses import dataclass
import ast


@dataclass
class CodeIssue:
    filename: str = None
    line: int = 0
    column: int = 0
    code: str = None
    message: str = None

    def __str__(self):
        patter = "{file}({line},{column}) {code}: {message}"
        return patter.format(
            file=self.filename,
            line=self.line,
            column=self.column,
            code=self.code,
            message=self.message,
        )


class AnalysisContext:
    def __init__(self, filename: str):
        self.filename = filename
        self.issues = []

    def add_issue(self, node: ast.AST, code: str, message: str):
        issue = CodeIssue(
            filename=self.filename,
            line=node.lineno,
            column=node.col_offset,
            code=code,
            message=message,
        )
        self.issues.append(issue)

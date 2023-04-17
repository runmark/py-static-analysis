from dataclasses import dataclass
import ast
from typing import List


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
        self.issues: List[CodeIssue] = []

    def add_issue(self, node: ast.AST, code: str, message: str, lineno: int = None):
        issue = CodeIssue(
            filename=self.filename,
            code=code,
            message=message,
            column=node.col_offset,
            line=lineno or node.lineno,
        )
        self.issues.append(issue)

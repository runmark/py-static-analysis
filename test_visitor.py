from unittest import TestCase

from model import AnalysisContext
import ast
from astxml import AstXml

from visitor import LineLengthVisitor


class VisitorMixin:
    visitor_type = None

    def run_visitor(self, code: str, xml_filename: str = None):
        self.assertIsNotNone(self.visitor_type, "Visitor type not defined.")

        self.ctx = AnalysisContext("test.py")
        visitor = LineLengthVisitor(self.ctx)
        ast_node = ast.parse(code)
        visitor.visit(ast_node)

        if xml_filename:
            AstXml(ast_node).save_file("dump/" + xml_filename)

    def assert_found_issue(self, lineno: int, code: str):
        for issue in self.ctx.issues:
            if issue.line == lineno and issue.code == code:
                return

        issues = "\n".join([str(x) for x in self.ctx.issues])
        self.fail(f"Expect issue {code} in line {lineno}, actual: {issues}")


class LineLengthVisitorTest(TestCase, VisitorMixin):
    visitor_type = LineLengthVisitor

    def test_visit(self):
        code = """
print('short line')
print('this is a very, very, very, very, very, very, very, very, very, very, very, very long line...')
print('this is a very, very, very, very, very, very, very, very, very, very, very, very long line...')
        """.strip()

        self.run_visitor(code, xml_filename="line-length.xml")
        self.assert_found_issue(2, "W0001")
        self.assert_found_issue(3, "W0001")

    def test_visit_docstring(self):
        code = """
def fn():
    '''
    This is a very, very, very, very, very, very, very, very, very, very, very, very long doc string
    The second line
    '''
    pass        
        """.strip()

        self.run_visitor(code, xml_filename="doc-string-length.xml")
        self.assert_found_issue(3, "W0001")

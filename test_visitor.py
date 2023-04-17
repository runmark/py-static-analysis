from unittest import TestCase

from model import AnalysisContext
import ast
from astxml import AstXml

from visitor import LineLengthVisitor, ExceptionTypeVisitor, VariableUsageVisitor


class VisitorMixin:
    visitor_type = None

    def run_visitor(self, code: str, xml_filename: str = None):
        self.assertIsNotNone(self.visitor_type, "Visitor type not defined.")

        self.ctx = AnalysisContext("test.py")
        visitor = self.visitor_type(self.ctx)
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

    def assert_no_issue(self):
        issue_count = len(self.ctx.issues)
        self.assertEqual(0, issue_count, f"Expected no issue, actual: {issue_count}")


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


class ExceptionTypeVisitorTest(TestCase, VisitorMixin):
    visitor_type = ExceptionTypeVisitor

    def test_no_handler(self):
        code = """print('hello')""".strip()
        self.run_visitor(code, xml_filename="exception-no-handler.xml")
        self.assert_no_issue()

    def test_handler_generic(self):
        code = """
try:
    calc()
except Exception as e:
    print(e)
        """.strip()

        self.run_visitor(code, xml_filename="exception-catch-generic.xml")
        self.assert_found_issue(3, "W0002")

    def test_catch_multiple_types_with_issue(self):
        code = """
try:
   calc()
except (Exception, ValueError) as e:
   print(e)
        """.strip()
        self.run_visitor(code, xml_filename="exception-catch-multi-with-issue.xml")
        self.assert_found_issue(3, "W0002")

    def test_catch_no_type(self):
        code = """
try:
   calc()
except:
   print(e)
        """.strip()
        self.run_visitor(code, xml_filename="exception-catch-no-type.xml")
        self.assert_found_issue(3, "W0002")


class VariableUsageVisitorTest(TestCase, VisitorMixin):
    visitor_type = VariableUsageVisitor

    def test_vars_all_used(self):
        code = """
def fn():
    name = 'user'
    print(name)        
        """.strip()
        self.run_visitor(code, xml_filename="var-used.xml")
        self.assert_no_issue()

    def test_vars_not_used(self):
        code = """
def fn():
    name, work = 'user', 'work'
    print('hello')        
        """.strip()
        self.run_visitor(code, xml_filename="vars-unused.xml")
        self.assert_found_issue(2, "W0003")

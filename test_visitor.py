from unittest import TestCase

from model import AnalysisContext
import ast
from astxml import AstXml

from visitor import LineLengthVisitor


class LineLengthVisitorTest(TestCase):
    def test_visit(self):
        code = """
print('short line')
print('this is a very, very, very, very, very, very, very, very, very, very, very, very long line...')
print('this is a very, very, very, very, very, very, very, very, very, very, very, very long line...')
        """.strip()

        ctx = AnalysisContext("test.py")
        visitor = LineLengthVisitor(ctx)
        ast_node = ast.parse(code)
        visitor.visit(ast_node)

        AstXml(ast_node).save_file("dump/line-length.xml")

        self.assertEqual(2, len(ctx.issues))

        issue = ctx.issues[0]
        self.assertEqual((2, "W0001"), (issue.line, issue.code))

    def test_visit_docstring(self):
        code = """
def fn():
    '''
    This is a very, very, very, very, very, very, very, very, very, very, very, very long doc string
    The second line
    '''
    pass        
        """.strip()

        ctx = AnalysisContext("test.py")
        visitor = LineLengthVisitor(ctx)

        ast_node = ast.parse(code)
        visitor.visit(ast_node)

        AstXml(ast_node).save_file("dump/doc-string-length.xml")

        self.assertEqual(1, len(ctx.issues))

        issue = ctx.issues[0]
        self.assertEqual((3, "W0001"), (issue.line, issue.code))

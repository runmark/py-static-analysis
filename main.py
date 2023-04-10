import ast

from astxml import AstXml

code = """
def add(a, b):
	print( a + b )
	return a + b
""".strip()


ast_node = ast.parse(code)
AstXml(ast_node).save_file("filename.xml")

import ast
import importlib.abc
import os
import sys


def import_from_file(file_path):
    """
    Import the specified file, with an unqualified module name.
    """
    folder = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    module_name = os.path.splitext(filename)[0]
    return import_module(folder, module_name)


def import_module(dir_path, module_name):
    """
    Import the specified module from the specified directory, rewriting
    assert statements where necessary.
    """
    filename = resolve_filename(dir_path, module_name)
    prune_sys_dot_modules(module_name, filename)
    if module_name in sys.modules:
        return sys.modules[module_name]

    return AssertionRewritingLoader(module_name, filename).load_module(module_name)


def resolve_filename(dir_path, module_name):
    filename = os.path.join(dir_path, *module_name.split('.'))
    if os.path.isdir(filename):  # it's a package
        filename = os.path.join(filename, '__init__.py')
    else:
        filename += '.py'
    return filename


def prune_sys_dot_modules(module_name, module_location):
    if module_name in sys.modules:
        existing_module = sys.modules[module_name]
        if not same_file(existing_module.__file__, module_location):
            del sys.modules[module_name]


def same_file(path1, path2):
    return os.path.realpath(path1) == os.path.realpath(path2)


class AssertionRewritingLoader(importlib.abc.FileLoader, importlib.abc.SourceLoader):
    # in Python 3.4, implementing get_code won't be necessary -
    # I could just override source_to_code.
    # When 3.4 gets officially released, maybe wrap this def in an if
    def get_code(self, fullname):
        source = self.get_source(fullname)
        path = self.get_filename(fullname)
        return self.source_to_code(source, path)

    def source_to_code(self, source, path='<string>'):
        parsed = ast.parse(source)
        transformer = AssertionRewriter()
        transformer.visit(parsed)

        return compile(parsed, path, 'exec', dont_inherit=True, optimize=0)

    def module_repr(self, module):
        return '<module {!r} from {!r}>'.format(module.__name__, module.__file__)


class AssertionRewriter(ast.NodeTransformer):
    def visit_Assert(self, assert_node):
        if assert_node.msg is not None:
            return assert_node

        statements = AssertionChildVisitor().visit(assert_node.test)

        for s in statements:
            ast.copy_location(s, assert_node)
            ast.fix_missing_locations(s)  # apply the same location to children
        return statements


class AssertionChildVisitor(ast.NodeVisitor):
    def visit(self, node):
        ret = super().visit(node)
        if ret is None:  # then it's not a node we know about
            return self.visit_unknown_node(node)
        return ret

    def visit_Compare(self, compare_node):
        if isinstance(compare_node.ops[0], ast.NotEq):
            format_string = 'Asserted {0} != {1} but found them to be equal'
        elif isinstance(compare_node.ops[0], ast.Eq):
            format_string = 'Asserted {0} == {1} but found them not to be equal'
        else:
            return None

        statements = []
        format_params = []
        for i, comparator in enumerate([compare_node.left] + compare_node.comparators):
            name = '@contexts_assertion_var' + str(i)
            statements.append(ast.Assign([ast.Name(name, ast.Store())], comparator))

            load_name = ast.Name(name, ast.Load())
            if i == 0:
                compare_node.left = load_name
            else:
                compare_node.comparators[i-1] = load_name
            format_params.append(ast.Call(func=ast.Name('repr', ast.Load()), args=[load_name], keywords=[]))

        msg = ast.Call(func=ast.Attribute(value=ast.Str(format_string), attr='format', ctx=ast.Load()), args=format_params, keywords=[])

        statements.append(ast.Assert(compare_node, msg))

        return statements

    def visit_Name(self, name_node):
        if name_node.id == 'False':
            msg = ast.Str("Explicitly asserted False")
            return [ast.Assert(name_node, msg)]

    def visit_unknown_node(self, node):
        format_string = "Asserted {} but found it not to be truthy"

        name = '@contexts_assertion_var'
        load_name = ast.Name(name, ast.Load())
        format_params = [ast.Call(func=ast.Name('repr', ast.Load()), args=[load_name], keywords=[])]
        msg = ast.Call(func=ast.Attribute(value=ast.Str(format_string), attr='format', ctx=ast.Load()), args=format_params, keywords=[])

        statements = [ast.Assign([ast.Name(name, ast.Store())], node), ast.Assert(ast.Name(name, ast.Load()), msg)]
        return statements

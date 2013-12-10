import ast
import contextlib
import os
import sys
import types


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
    # http://en.wikipedia.org/wiki/Greenspun's_tenth_rule applied to the import system :|

    filename = resolve_filename(dir_path, module_name)
    prune_sys_dot_modules(module_name, filename)
    if module_name in sys.modules:
        return sys.modules[module_name]

    module = create_module_object(module_name, filename)
    sys.modules[module_name] = module

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            source = f.read()
    except ImportError:
        raise
    except Exception as e:
        del sys.modules[module_name]
        raise ImportError from e

    parsed = ast.parse(source)
    transformer = AssertionRewriter()
    transformer.visit(parsed)

    code = compile(parsed, filename, 'exec', dont_inherit=True, optimize=0)

    try:
        exec(code, module.__dict__)
    except:
        del sys.modules[module_name]
        raise

    return module


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


def create_module_object(module_name, filename):
    module = types.ModuleType(module_name)
    module.__file__ = filename

    if '__init__.py' in filename:
        module.__package__ = module_name
        module.__path__ = [os.path.dirname(filename)]
    else:
        if '.' in module_name:
            module.__package__, _ = module_name.rsplit('.', 1)
        else:
            module.__package__ = ''

    return module


@contextlib.contextmanager
def prepend_folder_to_sys_dot_path(folder_path):
    sys.path.insert(0, folder_path)
    try:
        yield
    finally:
        sys.path.pop(0)


def same_file(path1, path2):
    return os.path.realpath(path1) == os.path.realpath(path2)


class AssertionRewriter(ast.NodeTransformer):
    def visit_Assert(self, assert_node):
        if assert_node.msg is not None:
            return assert_node

        statements, assert_node.msg = AssertionTestVisitor().visit(assert_node.test)

        statements.append(assert_node)
        for s in statements:
            ast.copy_location(s, assert_node)
            ast.fix_missing_locations(s)  # apply the same location to children
        return statements


class AssertionTestVisitor(ast.NodeVisitor):
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

        return_nodes = []
        format_params = []
        for i, comparator in enumerate([compare_node.left] + compare_node.comparators):
            name = '@contexts_assertion_var' + str(i)
            return_nodes.append(ast.Assign([ast.Name(name, ast.Store())], comparator))

            load_name = ast.Name(name, ast.Load())
            format_params.append(ast.Call(func=ast.Name('repr', ast.Load()), args=[load_name], keywords=[]))

        msg = ast.Call(func=ast.Attribute(value=ast.Str(format_string), attr='format', ctx=ast.Load()), args=format_params, keywords=[])

        return return_nodes, msg

    def visit_Name(self, node):
        if node.id == 'False':
            return [], ast.Str("Explicitly asserted False")

    def visit_unknown_node(self, node):
        format_string = "Asserted {} but found it not to be truthy"

        name = '@contexts_assertion_var'
        load_name = ast.Name(name, ast.Load())
        format_params = [ast.Call(func=ast.Name('repr', ast.Load()), args=[load_name], keywords=[])]
        msg = ast.Call(func=ast.Attribute(value=ast.Str(format_string), attr='format', ctx=ast.Load()), args=format_params, keywords=[])

        return [ast.Assign([ast.Name(name, ast.Store())], node)], msg

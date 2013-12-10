import ast
import contextlib
import os
import sys
import types


# http://en.wikipedia.org/wiki/Greenspun's_tenth_rule applied to the import system :|


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

    with open(filename, 'r', encoding='utf-8') as f:
        source = f.read()

    parsed = ast.parse(source)
    transformer = AssertionRewriter()
    transformer.visit(parsed)

    code = compile(parsed, filename, 'exec', dont_inherit=True, optimize=0)

    module = create_module_object(module_name, filename)

    exec(code, module.__dict__)
    sys.modules[module_name] = module
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
    def visit_Assert(self, node):
        if node.msg:
            return node
        msg = AssertionMessageGenerator().visit(node.test)
        node.msg = ast.Str(msg)
        return ast.fix_missing_locations(node)


class AssertionMessageGenerator(ast.NodeVisitor):
    def visit_Compare(self, node):
        if isinstance(node.left, ast.Num):
            left = node.left.n
        else:
            left = node.left.s
        if isinstance(node.comparators[0], ast.Num):
            right = node.comparators[0].n
        else:
            right = node.comparators[0].s
        return "Asserted {0} == {1} but found {0} != {1}.".format(repr(left), repr(right))

    def visit_Name(self, node):
        return "Explicitly asserted False"

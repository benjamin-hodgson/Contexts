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
    Load specified module from the specified directory
    """
    requested_file = resolve_file(dir_path, module_name)
    prune_sys_dot_modules(module_name, requested_file)

    if module_name in sys.modules:
        return sys.modules[module_name]

    with open(requested_file, 'r') as f:
        source = f.read()

    parsed = ast.parse(source)
    transformer = AssertionRewritingTransformer()
    transformer.visit(parsed)

    code = compile(parsed, requested_file, 'exec', dont_inherit=True, optimize=0)

    module = types.ModuleType(module_name)
    module.__file__ = requested_file

    if '__init__.py' in requested_file:
        module.__package__ = module_name
        module.__path__ = [os.path.dirname(requested_file)]
    else:
        if '.' in module_name:
            module.__package__, _ = module_name.rsplit('.', 1)
        else:
            module.__package__ = ''

    exec(code, module.__dict__)
    sys.modules[module_name] = module
    return module


def resolve_file(dir_path, module_name):
    requested_file = os.path.join(dir_path, *module_name.split('.'))
    if os.path.isdir(requested_file):  # it's a package
        requested_file = os.path.join(requested_file, '__init__.py')
    else:
        requested_file += '.py'
    return requested_file


def prune_sys_dot_modules(module_name, module_location):
    if module_name in sys.modules:
        existing_module = sys.modules[module_name]
        if not same_file(existing_module.__file__, module_location):
            del sys.modules[module_name]



@contextlib.contextmanager
def prepend_folder_to_sys_dot_path(folder_path):
    sys.path.insert(0, folder_path)
    try:
        yield
    finally:
        sys.path.pop(0)


def same_file(path1, path2):
    return os.path.realpath(path1) == os.path.realpath(path2)


class AssertionRewritingTransformer(ast.NodeTransformer):
    def visit_Assert(self, node):
        if node.msg:
            return node
        new_node = ast.copy_location(ast.Assert(node.test, ast.Str("Asserted False")), node)
        return ast.fix_missing_locations(new_node)

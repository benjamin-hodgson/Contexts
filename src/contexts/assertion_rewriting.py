import ast
import importlib.abc


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
        return ret if ret is not None else self.visit_unknown_node(node)

    def visit_Compare(self, compare_node):
        if isinstance(compare_node.ops[0], ast.NotEq):
            format_string = 'Asserted {0} != {1} but found them to be equal'
        elif isinstance(compare_node.ops[0], ast.Eq):
            format_string = 'Asserted {0} == {1} but found them not to be equal'
        elif isinstance(compare_node.ops[0], ast.Lt):
            format_string = "Asserted {0} < {1} but found {2}"
        elif isinstance(compare_node.ops[0], ast.LtE):
            format_string = "Asserted {0} <= {1} but found it to be greater"
        elif isinstance(compare_node.ops[0], ast.Gt):
            format_string = "Asserted {0} > {1} but found {2}"
        elif isinstance(compare_node.ops[0], ast.GtE):
            format_string = "Asserted {0} >= {1} but found it to be less"
        else:
            return None

        statements = []
        format_params = []
        new_comparators = []
        for i, comparator in enumerate([compare_node.left] + compare_node.comparators):
            name = '@contexts_assertion_var' + str(i)
            statements.append(self.assign(name, comparator))

            load_name = ast.Name(name, ast.Load())
            new_comparators.append(load_name)
            format_params.append(self.repr(load_name))

        if isinstance(compare_node.ops[0], ast.Lt):
            name = '@contexts_formatparam'
            ternary_expression = ast.IfExp(ast.Compare(new_comparators[0], [ast.Gt()], [new_comparators[1]]), ast.Str('it to be greater'), ast.Str('them to be equal'))
            statements.append(self.assign(name, ternary_expression))
            format_params.append(ast.Name(name, ast.Load()))
        if isinstance(compare_node.ops[0], ast.Gt):
            name = '@contexts_formatparam'
            ternary_expression = ast.IfExp(ast.Compare(new_comparators[0], [ast.Lt()], [new_comparators[1]]), ast.Str('it to be less'), ast.Str('them to be equal'))
            statements.append(self.assign(name, ternary_expression))
            format_params.append(ast.Name(name, ast.Load()))

        compare_node.left, *compare_node.comparators = new_comparators
        msg = self.format(format_string, format_params)

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
        msg = self.format(format_string, [self.repr(load_name)])

        statements = [self.assign(name, node), ast.Assert(ast.Name(name, ast.Load()), msg)]
        return statements

    def assign(self, name, expr_node):
        return ast.Assign([ast.Name(name, ast.Store())], expr_node)

    def repr(self, load_name_node):
        return ast.Call(func=ast.Name('repr', ast.Load()), args=[load_name_node], keywords=[])

    def format(self, string, format_params):
        return ast.Call(func=ast.Attribute(value=ast.Str(string), attr='format', ctx=ast.Load()), args=format_params, keywords=[])

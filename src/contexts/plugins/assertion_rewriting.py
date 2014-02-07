import ast
import importlib.abc
from .importing import Importer


class AssertionRewritingImporter(Importer):
    @classmethod
    def locate(cls):
        return (None, Importer)
    def initialise(self, args, env):
        return args.rewriting
    def get_loader(self, module_name, filename):
        return AssertionRewritingLoader(module_name, filename)


class AssertionRewritingLoader(importlib.machinery.SourceFileLoader):
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
        if len(compare_node.comparators) > 1:
            return

        format_string = self.formatstring_for_comparison(compare_node)
        if format_string is None:
            return

        statements = []
        format_params = []
        new_comparators = []
        for i, comparator in enumerate([compare_node.left] + compare_node.comparators):
            name = '@contexts_assertion_var' + str(i)
            statements.append(self.assign(name, comparator))
            new_comparators.append(self.load(name))
            format_params.append(self.repr(self.load(name)))

        name = '@contexts_formatparam'
        if isinstance(compare_node.ops[0], ast.Lt):
            ternary_expression = ast.IfExp(
                ast.Compare(new_comparators[0], [ast.Gt()],[new_comparators[1]]),
                ast.Str('it to be greater'),
                ast.Str('them to be equal')
            )
        elif isinstance(compare_node.ops[0], ast.Gt):
            ternary_expression = ast.IfExp(
                ast.Compare(new_comparators[0], [ast.Lt()], [new_comparators[1]]),
                ast.Str('it to be less'),
                ast.Str('them to be equal')
            )

        if isinstance(compare_node.ops[0], (ast.Lt, ast.Gt)):
            statements.append(self.assign(name, ternary_expression))
            format_params.append(self.load(name))

        compare_node.left, *compare_node.comparators = new_comparators
        msg = self.format(format_string, format_params)

        statements.append(ast.Assert(compare_node, msg))
        return statements

    def visit_Call(self, call_node):
        func_name = call_node.func
        if hasattr(func_name, 'id') and func_name.id == "isinstance":
            return [
                self.assign('@contexts_assertion_var1', call_node.args[0]),
                self.assign('@contexts_assertion_var2', call_node.args[1]),
                self.assign('@contexts_assertion_var3', self.clsname(self.getattr(self.load('@contexts_assertion_var1'), '__class__'))),
                self.assign('@contexts_assertion_var4', ast.IfExp(
                    ast.Call(func=self.load('isinstance'), args=[
                        self.load('@contexts_assertion_var2'),
                        self.load('tuple'),
                      ], keywords=[]),
                    ast.Call(func=self.load('tuple'), args=[
                        ast.GeneratorExp(self.clsname(self.load('@x')), [
                            ast.comprehension(ast.Name('@x', ast.Store()), self.load('@contexts_assertion_var2'), []),
                          ]),
                      ], keywords=[]),
                    self.clsname(self.load('@contexts_assertion_var2'))
                )),
                ast.Assert(
                    ast.Call(func=ast.Name(id='isinstance', ctx=ast.Load()), args=[
                        self.load('@contexts_assertion_var1'),
                        self.load('@contexts_assertion_var2'),
                    ], keywords=[]),
                    self.format('Asserted isinstance({0}, {1}) but found it to be a {2}', [
                        self.repr(self.load('@contexts_assertion_var1')),
                        ast.Call(func=self.getattr(self.repr(self.load('@contexts_assertion_var4')), 'replace'), args=[ast.Str("'"), ast.Str("")], keywords=[]),
                        self.load('@contexts_assertion_var3'),
                ])),
            ]

    def visit_Name(self, name_node):
        if name_node.id == 'False':
            msg = ast.Str("Explicitly asserted False")
            return [ast.Assert(name_node, msg)]

    def visit_UnaryOp(self, unaryop_node):
        if isinstance(unaryop_node.op, ast.Not):
            format_string = "Asserted not {} but found it to be truthy"
            name = '@contexts_assertion_var'
            statements = [self.assign(name, unaryop_node.operand)]
            msg = self.format(format_string, [self.repr(self.load(name))])
            statements.append(ast.Assert(ast.UnaryOp(ast.Not(), self.load(name)), msg))
            return statements

    def visit_unknown_node(self, node):
        format_string = "Asserted {} but found it to be falsy"
        name = '@contexts_assertion_var'
        statements = [self.assign(name, node)]
        msg = self.format(format_string, [self.repr(self.load(name))])
        statements.append(ast.Assert(self.load(name), msg))
        return statements

    def formatstring_for_comparison(self, compare_node):
        if isinstance(compare_node.ops[0], ast.NotEq):
            return 'Asserted {0} != {1} but found them to be equal'
        if isinstance(compare_node.ops[0], ast.Eq):
            return 'Asserted {0} == {1} but found them not to be equal'
        if isinstance(compare_node.ops[0], ast.Lt):
            return "Asserted {0} < {1} but found {2}"
        if isinstance(compare_node.ops[0], ast.LtE):
            return "Asserted {0} <= {1} but found it to be greater"
        if isinstance(compare_node.ops[0], ast.Gt):
            return "Asserted {0} > {1} but found {2}"
        if isinstance(compare_node.ops[0], ast.GtE):
            return "Asserted {0} >= {1} but found it to be less"
        if isinstance(compare_node.ops[0], ast.In):
            return "Asserted {0} in {1} but found it not to be present"
        if isinstance(compare_node.ops[0], ast.NotIn):
            return "Asserted {0} not in {1} but found it to be present"
        if isinstance(compare_node.ops[0], ast.Is):
            return "Asserted {0} is {1} but found them not to be the same"
        if isinstance(compare_node.ops[0], ast.IsNot):
            return "Asserted {0} is not {1} but found them to be the same"

    def assign(self, name, expr_node):
        return ast.Assign([ast.Name(name, ast.Store())], expr_node)

    def repr(self, load_name_node):
        return ast.Call(func=ast.Name('repr', ast.Load()), args=[load_name_node], keywords=[])

    def format(self, string, format_params):
        return ast.Call(func=self.getattr(ast.Str(string), 'format'), args=format_params, keywords=[])

    def clsname(self, node):
        return self.getattr(node, "__name__")

    def load(self, name):
        return ast.Name(name, ast.Load())

    def getattr(self, node, name):
        return ast.Attribute(node, name, ast.Load())

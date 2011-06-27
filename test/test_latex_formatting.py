#!/usr/bin/env python

"""
Tests of LaTeX formatting rules.
"""

# These are thin wrappers on top of unittest.TestCase and unittest.main
from ufltestcase import UflTestCase, main

from uflacs.utils.log import info, warning, error
from uflacs.utils.assertions import uflacs_assert

import ufl
from ufl.algorithms import preprocess_expression

def format_expression_as_test_latex(expr, variables=None):
    "This is a test specific function for formatting ufl to LaTeX."
    from uflacs.codeutils.expr_formatter import ExprFormatter
    from uflacs.codeutils.latex_format import LatexFormatterRules

    # Preprocessing expression before applying formatting.
    # In a compiler, one should probably assume that these
    # have been applied and use ExprFormatter directly.
    expr_data = preprocess_expression(expr)

    # This formatter is a multifunction with single operator
    # formatting rules for generic LaTeX formatting
    latex_formatter = LatexFormatterRules()

    # This final formatter implements a generic framework handling indices etc etc.
    variables = variables or {}
    expr_formatter = ExprFormatter(latex_formatter, variables)
    code = expr_formatter.visit(expr_data.preprocessed_expr)
    return code

class LatexFormatterTest(UflTestCase):

    def assertLatexEqual(self, expr, code, variables=None):
        r = format_expression_as_test_latex(expr, variables)
        self.assertEqual(code, r)

    def test_latex_formatting_of_literals(self):
        # Test literals
        self.assertLatexEqual(ufl.as_ufl(2), "2")
        self.assertLatexEqual(ufl.as_ufl(3.14), '3.14')
        self.assertLatexEqual(ufl.as_ufl(0), "0")
        # These are actually converted to int before formatting:
        self.assertLatexEqual(ufl.Identity(2)[0,0], "1")
        self.assertLatexEqual(ufl.Identity(2)[0,1], "0")
        self.assertLatexEqual(ufl.Identity(2)[1,0], "0")
        self.assertLatexEqual(ufl.Identity(2)[1,1], "1")
        self.assertLatexEqual(ufl.PermutationSymbol(3)[1,2,3], "1")
        self.assertLatexEqual(ufl.PermutationSymbol(3)[2,1,3], "-1")
        self.assertLatexEqual(ufl.PermutationSymbol(3)[1,1,3], "0")

    def test_latex_formatting_of_geometry(self):
        # Test geometry quantities
        x = ufl.cell1D.x
        self.assertLatexEqual(x, "x_0")
        x, y = ufl.cell2D.x
        self.assertLatexEqual(x, "x_0")
        self.assertLatexEqual(y, "x_1")
        nx, ny = ufl.cell2D.n
        self.assertLatexEqual(nx, "n_0")
        self.assertLatexEqual(ny, "n_1")
        Kv = ufl.cell2D.volume
        self.assertLatexEqual(Kv, r"K_{\text{vol}}")
        Kr = ufl.cell2D.circumradius
        self.assertLatexEqual(Kr, r"K_{\text{rad}}")

    def test_latex_formatting_of_form_arguments(self):
        # Test form arguments (faked for testing!)
        V = ufl.FiniteElement("CG", ufl.cell2D, 1)
        f = ufl.Coefficient(V).reconstruct(count=0)
        self.assertLatexEqual(f, r"\overset{0}{w}")
        v = ufl.Argument(V).reconstruct(count=0)
        self.assertLatexEqual(v, r"\overset{0}{v}")

        V = ufl.VectorElement("CG", ufl.cell2D, 1)
        f = ufl.Coefficient(V).reconstruct(count=1)
        self.assertLatexEqual(f[0], r"\overset{0}{w}_{0}") # Renumbered to 0...
        v = ufl.Argument(V).reconstruct(count=3)
        self.assertLatexEqual(v[1], r"\overset{0}{v}_{1}") # Renumbered to 0...

        V = ufl.TensorElement("CG", ufl.cell2D, 1)
        f = ufl.Coefficient(V).reconstruct(count=2)
        self.assertLatexEqual(f[1,0], r"\overset{0}{w}_{1 0}") # Renumbered to 0...
        v = ufl.Argument(V).reconstruct(count=3)
        self.assertLatexEqual(v[0,1], r"\overset{0}{v}_{0 1}") # Renumbered to 0...

        # TODO: Test mixed functions
        # TODO: Test tensor functions with symmetries

    def test_latex_formatting_of_arithmetic(self):
        x = ufl.triangle.x[0]
        self.assertLatexEqual(x + 3, "3 + x_0")
        self.assertLatexEqual(x * 2, "2 x_0")
        self.assertLatexEqual(x / 2, r"\frac{x_0}{2}")
        self.assertLatexEqual(x*x, r"pow(x_0, 2)") # TODO: Will gcc optimize this to x*x for us?
        self.assertLatexEqual(x**3, r"pow(x_0, 3)")
        # TODO: Test all basic operators

    def test_latex_formatting_of_cmath(self):
        x = ufl.triangle.x[0]
        self.assertLatexEqual(ufl.exp(x), r"exp(x_0)")
        self.assertLatexEqual(ufl.ln(x), r"\ln(x_0)")
        self.assertLatexEqual(ufl.sqrt(x), r"sqrt(x_0)")
        self.assertLatexEqual(abs(x), r"\|x_0\|")
        self.assertLatexEqual(ufl.sin(x), r"\sin(x_0)")
        self.assertLatexEqual(ufl.cos(x), r"\cos(x_0)")
        self.assertLatexEqual(ufl.tan(x), r"\tan(x_0)")
        self.assertLatexEqual(ufl.asin(x), r"\arcsin(x_0)")
        self.assertLatexEqual(ufl.acos(x), r"\arccos(x_0)")
        self.assertLatexEqual(ufl.atan(x), r"\arctan(x_0)")

    def test_latex_formatting_of_derivatives(self):
        x = ufl.triangle.x[0]
        # Test derivatives of basic operators
        self.assertLatexEqual(ufl.Identity(2)[0,0].dx(0), "0")
        self.assertLatexEqual(x.dx(0), "1")
        self.assertLatexEqual(x.dx(1), "0")
        self.assertLatexEqual(ufl.sin(x).dx(0), r"\cos(x_0)")

        # Test derivatives of form arguments
        V = ufl.FiniteElement("CG", ufl.cell2D, 1)
        f = ufl.Coefficient(V).reconstruct(count=0)
        self.assertLatexEqual(f.dx(0), r"\overset{0}{w}_{, 0}")
        v = ufl.Argument(V).reconstruct(count=3)
        self.assertLatexEqual(v.dx(1), r"\overset{0}{v}_{, 1}")
        # TODO: Test more derivatives
        # TODO: Test variable derivatives using diff

    def xtest_latex_formatting_of_conditionals(self):
        # Test conditional expressions
        self.assertLatexEqual(ufl.conditional(ufl.lt(x, 2), y, 3),
                    "x_0 < 2 ? x_1: 3")
        self.assertLatexEqual(ufl.conditional(ufl.gt(x, 2), 4+y, 3),
                    "x_0 > 2 ? 4 + x_1: 3")
        self.assertLatexEqual(ufl.conditional(ufl.And(ufl.le(x, 2), ufl.ge(y, 4)), 7, 8),
                    "x_0 <= 2 && x_1 >= 4 ? 7: 8")
        self.assertLatexEqual(ufl.conditional(ufl.Or(ufl.eq(x, 2), ufl.ne(y, 4)), 7, 8),
                    "x_0 == 2 || x_1 != 4 ? 7: 8")
        # TODO: Some tests of nested conditionals with correct precedences?

    def test_latex_formatting_precedence_handling(self):
        x, y = ufl.triangle.x
        # Test precedence handling with sums
        # Note that the automatic sorting is reflected in formatting!
        self.assertLatexEqual(y + (2 + x), "x_1 + (2 + x_0)")
        self.assertLatexEqual((x + 2) + y, "x_1 + (2 + x_0)")

        self.assertLatexEqual((2 + x) + (3 + y), "(2 + x_0) + (3 + x_1)")

        self.assertLatexEqual((x + 3) + 2 + y, "x_1 + (2 + (3 + x_0))")
        self.assertLatexEqual(2 + (x + 3) + y, "x_1 + (2 + (3 + x_0))")
        self.assertLatexEqual(2 + (3 + x) + y, "x_1 + (2 + (3 + x_0))")
        self.assertLatexEqual(y + (2 + (3 + x)), "x_1 + (2 + (3 + x_0))")

        self.assertLatexEqual(2 + x + 3 + y, "x_1 + (3 + (2 + x_0))")
        self.assertLatexEqual(2 + x + 3 + y, "x_1 + (3 + (2 + x_0))")

        # Test precedence handling with divisions
        # This is more stable than sums since there is no sorting.
        self.assertLatexEqual((x / 2) / 3, r"\frac{(\frac{x_0}{2})}{3}")
        self.assertLatexEqual(x / (y / 3), r"\frac{x_0}{(\frac{x_1}{3})}")
        self.assertLatexEqual((x / 2) / (y / 3), r"\frac{(\frac{x_0}{2})}{(\frac{x_1}{3})}")
        self.assertLatexEqual(x / (2 / y) / 3, r"\frac{(\frac{x_0}{(\frac{2}{x_1})})}{3}")

        # Test precedence handling with highest level types
        self.assertLatexEqual(ufl.sin(x), r"\sin(x_0)")
        self.assertLatexEqual(ufl.cos(x+2), r"\cos(2 + x_0)")
        self.assertLatexEqual(ufl.tan(x/2), r"\tan(\frac{x_0}{2})")
        self.assertLatexEqual(ufl.acos(x + 3 * y), r"\arccos(x_0 + 3 x_1)")
        self.assertLatexEqual(ufl.asin(ufl.atan(x**4)), r"\arcsin(\arctan(pow(x_0, 4)))")
        self.assertLatexEqual(ufl.sin(y) + ufl.tan(x), r"\sin(x_1) + \tan(x_0)")

        # Test precedence handling with mixed types
        self.assertLatexEqual(3 * (2 + x), "3 (2 + x_0)")
        self.assertLatexEqual((2 * x) + (3 * y), "2 x_0 + 3 x_1")
        self.assertLatexEqual(2 * (x + 3) * y, "x_1 (2 (3 + x_0))")
        self.assertLatexEqual(2 * (x + 3)**4 * y, "x_1 (2 pow(3 + x_0, 4))")
        # TODO: More tests covering all types and more combinations!

    def test_latex_formatting_of_variables(self):
        x, y = ufl.triangle.x
        # Test user-provided C variables for subexpressions
        # we can use variables for x[0], and sum, and power
        self.assertLatexEqual(x**2 + y**2, "x2 + y2", variables={x**2: 'x2', y**2: 'y2'})
        self.assertLatexEqual(x**2 + y**2, r"pow(z, 2) + y2", variables={x: 'z', y**2: 'y2'})
        self.assertLatexEqual(x**2 + y**2, "q", variables={x**2 + y**2: 'q'})
        # we can use variables in conditionals
        if 0:
            self.assertLatexEqual(ufl.conditional(ufl.Or(ufl.eq(x, 2), ufl.ne(y, 4)), 7, 8),
                                  "c1 || c2 ? 7: 8",
                                  variables={ufl.eq(x, 2): 'c1', ufl.ne(y, 4): 'c2'})
        # we can replace coefficients (formatted by user provided code)
        V = ufl.FiniteElement("CG", ufl.cell2D, 1)
        f = ufl.Coefficient(V).reconstruct(count=0)
        self.assertLatexEqual(f, "f", variables={f: 'f'})
        self.assertLatexEqual(f**3, r"pow(f, 3)", variables={f: 'f'})
        # variables do not replace derivatives of variable expressions
        self.assertLatexEqual(f.dx(0), r"\overset{0}{w}_{, 0}", variables={f: 'f'})
        # variables do replace variable expressions that are themselves derivatives
        self.assertLatexEqual(f.dx(0), "df", variables={f.dx(0): 'df'})

        # TODO: Test variables in more situations with indices and derivatives

    # TODO: Test various compound operators

if __name__ == "__main__":
    main()


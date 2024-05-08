import unittest

from itertools import repeat

from polygen.node import (
    Grammar,
    Rule,
    Identifier,
    Expression,
    Alt,
    Part,
    Class,
    Range,
    And,
    Not,
    ZeroOrOne,
    ZeroOrMore,
    OneOrMore,
    Repetition,
    Char
)

from polygen.tree_modifier import (
    InvalidRangeError,
    InvalidRepetitionError,
    RedefRulesError,
    UndefRulesError,
    SemanticError,
    TreeModifierError,
    ExpandClass,
    ReplaceRep,
    ReplaceZeroOrOne,
    ReplaceOneOrMore,
    EliminateAnd,
    CheckUndefRedef,
    ReplaceNestedExps,
    # TreeWriter  # TODO: test
)


class TestExpandClass(unittest.TestCase):
    def test_simple_range(self):
        A = Char('a')
        tree = Part(prime=Class(Range(A)))
        clue = Part(prime=Expression(Alt(Part(prime=A))))
        rule = ExpandClass()

        node = tree.prime
        rule.visit_Class(node)
        self.assertEqual(tree, clue)
        self.assertEqual(tree.prime.parent, tree)

    def test_range_abc(self):
        A, B, C = Char('a'), Char('b'), Char('c')
        tree = Part(prime=Class(Range(A, C)))
        clue = Part(
            prime=Expression(
                Alt(Part(prime=A)),
                Alt(Part(prime=B)),
                Alt(Part(prime=C))
            )
        )
        rule = ExpandClass()

        node = tree.prime
        rule.visit_Class(node)
        self.assertEqual(tree, clue)
        self.assertEqual(tree.prime.parent, tree)

    def test_two_ranges(self):
        A, B, C = Char('a'), Char('b'), Char('c')
        _0, _1, _2 = Char('0'), Char('1'), Char('2')
        tree = Part(prime=Class(Range(A, C), Range(_0, _2)))
        clue = Part(
            prime=Expression(
                Alt(Part(prime=_0)),
                Alt(Part(prime=_1)),
                Alt(Part(prime=_2)),
                Alt(Part(prime=A)),
                Alt(Part(prime=B)),
                Alt(Part(prime=C))
            )
        )
        rule = ExpandClass()

        node = tree.prime
        rule.visit_Class(node)
        self.assertEqual(tree, clue)
        self.assertEqual(tree.prime.parent, tree)

    def test_intersecting_ranges(self):
        A, B, C, D = Char('a'), Char('b'), Char('c'), Char('d')
        tree = Part(prime=Class(Range(A, C), Range(B, D)))
        clue = Part(
            prime=Expression(
                Alt(Part(prime=A)),
                Alt(Part(prime=B)),
                Alt(Part(prime=C)),
                Alt(Part(prime=D))
            )
        )
        rule = ExpandClass()

        node = tree.prime
        rule.visit_Class(node)
        self.assertEqual(tree, clue)

    def test_invalid_range(self):
        B, C = Char('b'), Char('c')
        rng = Range(C, B)
        tree = Part(prime=Class(rng))
        rule = ExpandClass()

        node = tree.prime

        with self.assertRaises(InvalidRangeError) as raised_exc:
            rule.visit_Class(node)

        exception = raised_exc.exception
        self.assertEqual(exception.node, rng)


class TestReplaceRep(unittest.TestCase):
    def test_apply_repetition_without_end(self):
        E = Char('e')
        tree = Part(prime=E, quant=Repetition(3))
        node = tree.quant
        clue = Part(
            prime=Expression(
                Alt(*repeat(Part(prime=E), 3))
            )
        )
        rule = ReplaceRep()

        rule.visit_Repetition(node)
        self.assertEqual(tree, clue)

    def test_apply_repetition_with_end(self):
        E = Char('e')
        tree = Part(prime=E, quant=Repetition(2, 6))
        clue = Part(
            prime=Expression(
                Alt(
                    *repeat(Part(prime=E), 2),
                    Part(prime=Expression(
                        Alt(*repeat(Part(prime=E), 4))
                    ), quant=ZeroOrOne())
                )
            )
        )
        node = tree.quant
        rule = ReplaceRep()

        rule.visit_Repetition(node)
        self.assertEqual(tree, clue)

    def test_apply_repetition_invalid_end(self):
        E = Char('e')
        rule = ReplaceRep()
        rep = Repetition(3, 2)
        part = Part(prime=E, quant=rep)
        node = part.quant
        with self.assertRaises(InvalidRepetitionError) as context:
            rule.visit_Repetition(node)

        exception = context.exception
        self.assertEqual(exception.node, rep)


class TestReplaceZeroOrOne(unittest.TestCase):
    def test_eliminate(self):
        E = Char('e')
        tree = Part(prime=E, quant=ZeroOrOne())
        node = tree.quant
        clue = Part(
            prime=Expression(
                Alt(Part(prime=E)),
                Alt()
            )
        )

        rule = ReplaceZeroOrOne()
        rule.visit_ZeroOrOne(node)

        self.assertEqual(tree, clue)


class TestReplaceOneOrMore(unittest.TestCase):
    def test_replace(self):
        E = Char('e')
        tree = Part(prime=E, quant=OneOrMore())
        node = tree.quant
        clue = Part(
            prime=Expression(
                Alt(
                    Part(prime=E),
                    Part(prime=E, quant=ZeroOrMore())
                )
            )
        )

        rule = ReplaceOneOrMore()
        rule.visit_OneOrMore(node)

        self.assertEqual(tree, clue)

    def test_with_multiple_parts(self):
        Def = Identifier('Definition')
        tree = Expression(
            Alt(
                Part(prime=Identifier('Spacing')),
                Part(prime=Def, quant=OneOrMore()),
                Part(prime=Identifier('EndOfFile'))
            )
        )
        node = tree.alts[0].parts[1].quant
        clue = Expression(
            Alt(
                Part(prime=Identifier('Spacing')),
                Part(prime=Expression(
                    Alt(
                        Part(prime=Def),
                        Part(prime=Def, quant=ZeroOrMore())
                    )
                )),
                Part(prime=Identifier('EndOfFile'))
            )
        )

        rule = ReplaceOneOrMore()
        rule.visit_OneOrMore(node)

        self.assertEqual(tree, clue)


class TestEliminateAnd(unittest.TestCase):
    def test_rule(self):
        E = Char('e')
        tree = Part(pred=And(), prime=E)
        node = tree.pred
        clue = Part(
            pred=Not,
            prime=Expression(
                Alt(
                    Part(pred=Not(), prime=E)
                )
            )
        )

        rule = EliminateAnd()
        rule.visit_And(node)

        self.assertTrue(node, clue)


class TestCheckUndefRedef(unittest.TestCase):
    def test_undef(self):
        A, B = Identifier('A'), Identifier('B')
        exp = Expression(Alt(Part(prime=B)))
        R = Rule(A, exp)
        g = Grammar(R)

        rule = CheckUndefRedef()

        rule.visit_Identifier(A)
        rule.visit_Identifier(B)

        with self.assertRaises(UndefRulesError) as raised_exc:
            rule.visit_Grammar(g)

        exception = raised_exc.exception
        self.assertEqual(exception.rules, {B: R})

    def test_redef(self):
        A = Identifier('A')
        exp = Expression(Alt(Part(prime=Char('c'))))

        A1 = A.copy()
        A2 = A.copy()
        R1 = Rule(A1, exp.copy())
        R2 = Rule(A2, exp.copy())
        g = Grammar(R1, R2)

        rule = CheckUndefRedef()

        rule.visit_Identifier(A1)
        rule.visit_Identifier(A2)

        with self.assertRaises(RedefRulesError) as raised_exc:
            rule.visit_Grammar(g)

        exception = raised_exc.exception
        self.assertEqual(exception.rules, {A1: [R1, R2]})


class TestReplaceNestedExps(unittest.TestCase):
    def test_simple_number_rule(self):
        number_id = Identifier('Number')
        number_gen_id = Identifier('Number__GEN_1')

        nested_exp = Expression(Alt(Part(prime=Char('0'))),
                                Alt(Part(prime=Char('1'))))

        # nested_exp should hold initial tree's node as parent,
        # do not copy here
        tree = Grammar(
            Rule(number_id.copy(),
                 Expression(Alt(Part(prime=nested_exp))))
        )

        clue = Grammar(
            Rule(number_id.copy(),
                 Expression(Alt(Part(prime=number_gen_id.copy())))),
            Rule(number_gen_id, nested_exp.copy())
        )

        rule = ReplaceNestedExps()

        node = nested_exp
        rule.visit_Expression(node)

        rule.visit_Grammar(tree)

        self.assertEqual(tree, clue)

    def test_complicated_number_rule(self):
        number_id = Identifier('Number')
        number_gen_id = Identifier('Number__GEN_1')

        nested_exp = Expression(Alt(Part(prime=Char('0'))),
                                Alt(Part(prime=Char('1'))))

        nested_exp1 = nested_exp.copy()
        nested_exp2 = nested_exp.copy()

        tree = Grammar(
            Rule(number_id.copy(),
                 Expression(
                     Alt(Part(prime=nested_exp1)),
                     Alt(Part(prime=nested_exp2, quant=ZeroOrMore())))
                 )
        )

        clue = Grammar(
            Rule(number_id.copy(),
                 Expression(
                     Alt(Part(prime=number_gen_id.copy())),
                     Alt(Part(prime=number_gen_id.copy(), quant=ZeroOrMore())))
                 ),
            Rule(number_gen_id, nested_exp.copy())
        )

        rule = ReplaceNestedExps()

        node = nested_exp1
        rule.visit_Expression(node)

        node = nested_exp2
        rule.visit_Expression(node)

        rule.visit_Grammar(tree)

        self.assertEqual(tree, clue)

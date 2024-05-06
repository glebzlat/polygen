import re

from contextlib import contextmanager
from keyword import iskeyword

from .node import (
    Grammar,
    Rule,
    Identifier,
    AnyChar,
    Char,
    String,
    Not,
    And,
    ZeroOrOne,
    ZeroOrMore,
    OneOrMore
)

_UNESCAPED_DOUBLE_QUOTE_RE = re.compile(r'(?<!\\)"')


def wrap_string(s: str):
    if _UNESCAPED_DOUBLE_QUOTE_RE.match(s):
        s = s.replace('"', '\\"')
    return '"' + s + '"'


class GeneratorError(Exception):
    pass


class PythonGenerator:
    def __init__(self, stream=None):
        self.indentation = ''
        self.stream = stream

    def put(self, *args, newline=True, indent=True):
        if indent:
            print(end=self.indentation, file=self.stream)
        print(*args, end='', file=self.stream)
        if newline:
            print(file=self.stream)

    @contextmanager
    def indent(self, level: int = 1):
        save = self.indentation
        try:
            self.indentation += '    ' * level
            yield
        finally:
            self.indentation = save

    def generate(self, grammar: Grammar):
        for i, rule in enumerate(grammar):
            self.gen_rule(i, rule)

    def gen_rule(self, rule_index: int, rule: Rule):
        if rule_index != 0:
            self.put(indent=False)

        self.put('@memoize')
        self.put(f'def _{rule.name.string}(self):')

        with self.indent():
            self.put('pos = self._mark()')
            for i, alt in enumerate(rule.rhs):
                self.gen_alt(alt, rule, i)
            self.put('return None')

    def gen_alt(self, alt, rule, alt_index):
        put_newline = len(alt) > 1

        self.put('if (', newline=put_newline)
        variables = []
        with self.indent():
            for i, part in enumerate(alt):
                self.gen_part(part, i, variables, put_newline)
        self.put('):', indent=put_newline)

        with self.indent():
            retval = ', '.join(variables)
            # if alt.metarule:
            #     metarule = wrap_string(alt.metarule)
            #     if retval:
            #         self.put(f'return self._action({metarule}, {retval})')
            #     else:
            #         self.put(f'return self._action({metarule})')
            # else:
            self.put(f'return ({retval})')
        self.put('self._reset(pos)')

    def gen_part(self, part, part_index, variables, newline):
        parts = []

        cond = ''
        if type(part.pred) is Not:
            parts += 'self._lookahead', False
        elif type(part.pred) is And:
            parts += 'self._lookahead', True
        else:
            cond = 'is not None'

        if type(part.quant) is ZeroOrOne:
            parts.append('self._maybe')
        elif type(part.quant) is ZeroOrMore:
            parts += 'self._loop', False
        elif type(part.quant) is OneOrMore:
            parts += 'self._loop', True

        if part.metaname:
            key = part.metaname
            if iskeyword(key):
                key = f'_{key}'
            if key in variables:
                raise GeneratorError
        else:
            var = None

        def create_var():
            nonlocal var
            index = len(variables)
            var = f'_{index}'
            variables.append(var)

        if type(part.prime) is Char:
            parts += 'self._expectc', part.prime
            create_var()
        elif type(part.prime) is Identifier:
            id = part.prime
            parts.append(f'self._{id.string}')
            create_var()
        elif type(part.prime) is String:
            parts += 'self._expects', part.prime
            create_var()
        elif type(part.prime) is AnyChar:
            parts.append('self._expectc')
            create_var()
        else:
            raise GeneratorError('unsupported node type', part.prime)

        fn, args = parts[0], ', '.join(str(i) for i in parts[1:])
        op = 'and' if part_index else ''
        call = f'{fn}({args})'
        assignment = f'({var} := {call})' if var else call

        string = ' '.join(filter(None, (op, assignment, cond)))
        self.put(string, newline=newline, indent=newline)

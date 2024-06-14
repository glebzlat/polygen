# This is automatically generated code, do not edit.
# Generated by Polygen 0.1.0
# 2024-06-12T20:01

from __future__ import annotations

from typing import Optional
from functools import wraps

from polygen.reader import Reader
from .node import (
    Grammar,
    Rule,
    MetaRef,
    MetaRule,
    Expr,
    Alt,
    NamedItem,
    Id,
    String,
    Char,
    AnyChar,
    Class,
    Range,
    ZeroOrOne,
    ZeroOrMore,
    OneOrMore,
    Repetition,
    And,
    Not
)

__all__ = ['Parser']


class Success:
    """Parsing result wrapper."""

    def __init__(self, value=None):
        self.value = value

    def __repr__(self):
        return f'Success({self.value})'

    def __str__(self):
        return repr(self)


def _memoize(fn):

    @wraps(fn)
    def wrapper(self, *args):
        pos = self._mark()
        key = (fn, args, pos)
        memo = self._memos.get(key)
        if memo is None:
            result = fn(self, *args)
            endpos = self._mark()
            self._memos[key] = result, endpos
        else:
            result, endpos = memo
            self._reset(endpos)

        if result is not None:
            if type(result) is not Success:
                return Success(result)
        return result

    return wrapper


class _LR:
    def __init__(self, seed, rule, head):
        self.seed = seed
        self.rule = rule
        self.head = head

    def __repr__(self):
        return f'_LR(seed={self.seed}, rule={self.rule}, head={self.head})'

    def __str__(self):
        return repr(self)


class _Head:
    def __init__(self, rule, involved_set, eval_set):
        self.rule = rule
        self.involved_set = involved_set
        self.eval_set = eval_set

    def __repr__(self):
        return f'_Head({self.rule}, {self.involved_set}, {self.eval_set})'

    def __str__(self):
        return repr(self)


def _memoize_lr(fn):
    # The algorithm is taken from "Packrat parsers can support left recursion"
    # https://dl.acm.org/doi/10.1145/1328408.1328424

    def wrap(obj):
        if obj is not None:
            if type(obj) is not Success:
                return Success(obj)
        return obj

    rule = fn.__name__

    def recall(self, args):
        pos = self._mark()
        key = (fn, args, pos)
        m = self._memos.get(key)
        head = self._heads.get(pos)

        # If not growing a seed parse, just return what is stored
        # in the memo table
        if head is None:
            return m

        # Do not evaluate any rule that is not involved in This
        # left recursion
        if m is None and rule not in head.involved_set | {head.rule}:
            return None, pos

        # Allow involved rules to be evaluated, but only once,
        # during a seed-growing iteration
        if rule in head.eval_set:
            head.eval_set.remove(rule)
            result = fn(self, *args)
            endpos = self._mark()
            m = result, endpos

        return m

    @wraps(fn)
    def wrapper_lr(self, *args):
        m = recall(self, args)
        if m is None:
            pos = self._mark()
            key = (fn, args, pos)

            # Create a new LR and push in onto
            # the rule invocation stack
            lr = _LR(None, rule, None)
            self._lrstack.append(lr)

            # Memoize lr, then evaluate rule
            self._memos[key] = lr, pos
            result = fn(self, *args)
            self._lrstack.pop()
            endpos = self._mark()
            self._memos[key] = lr, endpos

            if lr.head is not None:
                lr.seed = result
                return lr_answer(self, args, key, pos)
            else:
                self._memos[key] = result, endpos
                return wrap(result)

        else:
            result, pos = m
            self._reset(pos)
            if type(result) is _LR:
                setup_lr(self, result)
                return wrap(result.seed)
            else:
                return wrap(result)

    def setup_lr(self, lr):
        if lr.head is None:
            lr.head = _Head(rule, set(), set())
        for i in reversed(self._lrstack):
            if i.head == lr.head:
                break
            i.head = lr.head
            lr.head.involved_set.add(i.rule)

    def lr_answer(self, args, key, pos):
        result, lastpos = self._memos[key]
        if result.head.rule != rule:
            return result.seed
        else:
            self._memos[key] = result.seed, lastpos
            if result.seed is None:
                return None
            return grow_lr(self, args, key, result.head, pos)

    def grow_lr(self, args, key, head, pos):
        result, _ = self._memos[key]
        self._heads[pos] = head

        self._memos[key] = lastres, lastpos = result, pos
        while True:
            self._reset(pos)
            head.eval_set = head.involved_set.copy()
            result = fn(self, *args)
            endpos = self._mark()
            if result is None or endpos <= lastpos:
                break
            self._memos[key] = lastres, lastpos = result, endpos

        result = lastres
        self._reset(lastpos)
        self._heads.pop(pos)

        return result

    return wrapper_lr


class Parser:

    def __init__(self, stream, actions=None):
        self._memos = {}

        self._heads = {}
        self._lrstack = []

        self._reader = Reader(stream)
        self._chars: list[str] = []
        self._pos = 0

    @_memoize
    def _expectc(self, char: str | None = None) -> Success | None:
        if c := self._peek_char():
            if char is None or c == char:
                self._pos += 1
                return Success(c)
        return None

    @_memoize
    def _expects(self, string: str) -> Success | None:
        pos = self._mark()
        for c in string:
            if c != self._peek_char():
                self._reset(pos)
                return None
            self._pos += 1
        return Success(string)

    def _lookahead(self, positive, fn, *args) -> Success | None:
        pos = self._mark()
        ok = fn(*args) is not None
        self._reset(pos)
        if ok == positive:
            return Success()
        return None

    def _loop(self, nonempty, fn, *args) -> Success | None:
        pos = lastpos = self._mark()
        nodes = []
        while (node := fn(*args)) is not None and self._mark() > lastpos:
            # Unwrap nodes, removing empty wrappers
            if node.value is not None:
                nodes.append(node.value)
            lastpos = self._mark()
        if len(nodes) >= nonempty:
            return Success(nodes)
        self._reset(pos)
        return None

    def _rep(self, beg, end, fn, *args) -> Success | None:
        end = beg if end is None else end
        pos = lastpos = self._mark()
        count = 0
        nodes = []
        while (node := fn(*args)) is not None and self._mark() > lastpos:
            nodes.append(node)
            lastpos = self._mark()
            count += 1
        if count >= beg and count <= end:
            # Unwrap nodes, removing empty wrappers
            nodes = tuple(n.value for n in nodes if n.value is not None)
            return Success(nodes)
        self._reset(pos)
        return None

    def _ranges(self, *ranges):
        char = self._peek_char()
        if char is None:
            return None
        for beg, end in ranges:
            if char >= beg and char <= end:
                return Success(self._get_char())

    def _maybe(self, fn, *args):
        result = fn(*args)
        return Success(result.value if result is not None else result)

    def _get_char(self) -> str | None:
        char = self._peek_char()
        self._pos += 1
        return char

    def _peek_char(self) -> str | None:
        if self._pos == len(self._chars):
            self._chars.append(next(self._reader, None))
        return self._chars[self._pos]

    def _mark(self) -> int:
        return self._pos

    def _reset(self, pos: int):
        self._pos = pos

    def parse(self) -> Success:
        return self._Grammar()

    @_memoize
    def _Grammar(self):
        _begin_pos = self._mark()
        if (
            self._Spacing() is not None
            and (entity := self._loop(True, self._Entity)) is not None
            and (endoffile := self._EndOfFile()) is not None
        ):
            entity = entity.value
            endoffile = endoffile.value

            # grammar_action
            rules = (r for r in entity if isinstance(r, Rule))
            metarules = (r for r in entity if isinstance(r, MetaRule))
            return Grammar(rules, metarules)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _Entity(self):
        _begin_pos = self._mark()
        if ((definition := self._Definition()) is not None):
            definition = definition.value
            return Success(definition)
        self._reset(_begin_pos)
        if ((metadef := self._MetaDef()) is not None):
            metadef = metadef.value
            return Success(metadef)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _Definition(self):
        _begin_pos = self._mark()
        if (
            (directive := self._loop(False, self._Directive)) is not None
            and (identifier := self._Identifier()) is not None
            and self._LEFTARROW() is not None
            and (expression := self._Expression()) is not None
        ):
            directive = directive.value
            identifier = identifier.value
            expression = expression.value

            # def_action
            ignore = "ignore" in directive
            entry = "entry" in directive
            return Rule(identifier, expression, ignore=ignore, entry=entry)
        self._reset(_begin_pos)
        if ((metadef := self._MetaDef()) is not None):
            metadef = metadef.value
            return Success(metadef)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _Directive(self):
        _begin_pos = self._mark()
        if (
            self._AT() is not None
            and (dirname := self._DirName()) is not None
            and self._Spacing() is not None
        ):
            dirname = dirname.value

            # directive_action
            return dirname.value
        self._reset(_begin_pos)
        return None

    @_memoize
    def _DirName(self):
        _begin_pos = self._mark()
        if ((identifier := self._Identifier()) is not None):
            identifier = identifier.value
            return Success(identifier)
        self._reset(_begin_pos)
        return None

    @_memoize_lr
    def _Expression(self):
        _begin_pos = self._mark()
        if (
            (sequence := self._Sequence()) is not None
            and (seqs := self._loop(False, self._Expression__GEN_1)) is not None
        ):
            sequence = sequence.value
            seqs = seqs.value

            # expr_action
            return Expr((sequence, *seqs))
        self._reset(_begin_pos)
        return None

    @_memoize_lr
    def _Sequence(self):
        _begin_pos = self._mark()
        if (
            (parts := self._loop(False, self._Prefix)) is not None
            and (m := self._maybe(self._MetaRule)) is not None
        ):
            parts = parts.value
            m = m.value

            # sequence_action
            return Alt(parts, metarule=m)
        self._reset(_begin_pos)
        return None

    @_memoize_lr
    def _Prefix(self):
        _begin_pos = self._mark()
        if (
            (metaname := self._maybe(self._MetaName)) is not None
            and (lookahead := self._maybe(self._Prefix__GEN_1)) is not None
            and (suffix := self._Suffix()) is not None
        ):
            metaname = metaname.value
            lookahead = lookahead.value
            suffix = suffix.value

            # prefix_action
            obj = lookahead(suffix) if lookahead is not None else suffix
            return NamedItem(metaname, obj)
        self._reset(_begin_pos)
        return None

    @_memoize_lr
    def _Suffix(self):
        _begin_pos = self._mark()
        if (
            (primary := self._Primary()) is not None
            and (q := self._maybe(self._Suffix__GEN_1)) is not None
        ):
            primary = primary.value
            q = q.value

            # suffix_action
            return q(primary) if q is not None else primary
        self._reset(_begin_pos)
        return None

    @_memoize_lr
    def _Primary(self):
        _begin_pos = self._mark()
        if (
            (identifier := self._Identifier()) is not None
            and self._lookahead(False, self._LEFTARROW)
        ):
            identifier = identifier.value
            return Success(identifier)
        self._reset(_begin_pos)
        if (
            self._OPEN() is not None
            and (expression := self._Expression()) is not None
            and self._CLOSE() is not None
        ):
            expression = expression.value
            return Success(expression)
        self._reset(_begin_pos)
        if ((literal := self._Literal()) is not None):
            literal = literal.value
            return Success(literal)
        self._reset(_begin_pos)
        if ((_class := self._Class()) is not None):
            _class = _class.value
            return Success(_class)
        self._reset(_begin_pos)
        if ((dot := self._DOT()) is not None):
            dot = dot.value
            return Success(dot)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _MetaName(self):
        _begin_pos = self._mark()
        if (
            (identifier := self._Identifier()) is not None
            and self._SEMI() is not None
        ):
            identifier = identifier.value
            return Success(identifier)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _MetaRule(self):
        _begin_pos = self._mark()
        if (
            (_1 := self._expects("${")) is not None
            and (expr := self._loop(False, self._MetaRule__GEN_1)) is not None
            and (_2 := self._expectc('}')) is not None
            and self._Spacing() is not None
        ):
            _1 = _1.value
            expr = expr.value
            _2 = _2.value

            # metarule_def_action
            return MetaRule(None, ''.join(expr))
        self._reset(_begin_pos)
        if (
            (_1 := self._expectc('$')) is not None
            and self._Spacing() is not None
            and (identifier := self._Identifier()) is not None
            and self._lookahead(False, self._expectc, '{')
        ):
            _1 = _1.value
            identifier = identifier.value

            # metarule_ref_action
            # XX CHANGE
            return MetaRef(identifier)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _MetaDef(self):
        _begin_pos = self._mark()
        if (
            (_1 := self._expectc('$')) is not None
            and self._Spacing() is not None
            and (identifier := self._Identifier()) is not None
            and (expr := self._MetaDefBody()) is not None
        ):
            _1 = _1.value
            identifier = identifier.value
            expr = expr.value

            # metadef_action
            return MetaRule(identifier, expr)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _MetaDefBody(self):
        _begin_pos = self._mark()
        if (
            (_1 := self._expectc('{')) is not None
            and (expr := self._loop(False, self._MetaRule__GEN_1)) is not None
            and (_2 := self._expectc('}')) is not None
            and self._Spacing() is not None
        ):
            _1 = _1.value
            expr = expr.value
            _2 = _2.value

            # metadef_body_action
            return ''.join(expr)
        self._reset(_begin_pos)
        return None

    @_memoize_lr
    def _NestedBody(self):
        _begin_pos = self._mark()
        if (
            (_1 := self._expectc('{')) is not None
            and (body := self._loop(False, self._MetaRule__GEN_1)) is not None
            and (_2 := self._expectc('}')) is not None
        ):
            _1 = _1.value
            body = body.value
            _2 = _2.value

            # nested_body_action
            string = ''.join(body)
            return f"{{{string}}}"
        self._reset(_begin_pos)
        return None

    @_memoize
    def _Identifier(self):
        _begin_pos = self._mark()
        if (
            (start := self._IdentStart()) is not None
            and (cont := self._loop(False, self._IdentCont)) is not None
            and self._Spacing() is not None
        ):
            start = start.value
            cont = cont.value

            # ident_action
            return Id(''.join((start, *cont)))
        self._reset(_begin_pos)
        return None

    @_memoize
    def _IdentStart(self):
        _begin_pos = self._mark()
        if ((_1 := self._ranges(('a', 'z'), ('A', 'Z'), ('_', '_'))) is not None):
            _1 = _1.value
            return Success(_1)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _IdentCont(self):
        _begin_pos = self._mark()
        if ((identstart := self._IdentStart()) is not None):
            identstart = identstart.value
            return Success(identstart)
        self._reset(_begin_pos)
        if ((_1 := self._ranges(('0', '9'))) is not None):
            _1 = _1.value
            return Success(_1)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _Literal(self):
        _begin_pos = self._mark()
        if (
            (_1 := self._ranges(("'", "'"))) is not None
            and (chars := self._loop(False, self._Literal__GEN_1)) is not None
            and (_2 := self._ranges(("'", "'"))) is not None
            and self._Spacing() is not None
        ):
            _1 = _1.value
            chars = chars.value
            _2 = _2.value

            # literal_action
            if len(chars) == 1:
              return chars[0]
            return String(chars)
        self._reset(_begin_pos)
        if (
            (_1 := self._ranges(('"', '"'))) is not None
            and (chars := self._loop(False, self._Literal__GEN_2)) is not None
            and (_2 := self._ranges(('"', '"'))) is not None
            and self._Spacing() is not None
        ):
            _1 = _1.value
            chars = chars.value
            _2 = _2.value

            # literal_action
            if len(chars) == 1:
              return chars[0]
            return String(chars)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _Class(self):
        _begin_pos = self._mark()
        if (
            (_1 := self._expectc('[')) is not None
            and (ranges := self._loop(False, self._Class__GEN_1)) is not None
            and (_2 := self._expectc(']')) is not None
            and self._Spacing() is not None
        ):
            _1 = _1.value
            ranges = ranges.value
            _2 = _2.value

            # class_action
            return Class(ranges)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _Range(self):
        _begin_pos = self._mark()
        if (
            (beg := self._Char()) is not None
            and (_1 := self._expectc('-')) is not None
            and (end := self._Char()) is not None
        ):
            beg = beg.value
            _1 = _1.value
            end = end.value

            # range_2_action
            return Range(beg, end)
        self._reset(_begin_pos)
        if ((beg := self._Char()) is not None):
            beg = beg.value

            # range_1_action
            return Range(beg)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _Char(self):
        _begin_pos = self._mark()
        if (
            (_1 := self._expectc('\\')) is not None
            and (char := self._ranges(('n', 'n'), ('r', 'r'), ('t', 't'), ("'", "'"), ('"', '"'), ('[', '['), (']', ']'), ('\\', '\\'))) is not None
        ):
            _1 = _1.value
            char = char.value

            # esc_char_action
            chr_map = {
                'n': '\n',
                'r': '\r',
                't': '\t',
            }

            return Char(chr_map.get(char, char))
        self._reset(_begin_pos)
        if (
            (_1 := self._expectc('\\')) is not None
            and (char1 := self._ranges(('0', '2'))) is not None
            and (char2 := self._ranges(('0', '7'))) is not None
            and (char3 := self._ranges(('0', '7'))) is not None
        ):
            _1 = _1.value
            char1 = char1.value
            char2 = char2.value
            char3 = char3.value

            # oct_char_action_1
            string = ''.join((char1, char2, char3))
            return Char(int(string, base=8))
        self._reset(_begin_pos)
        if (
            (_1 := self._expectc('\\')) is not None
            and (char1 := self._ranges(('0', '7'))) is not None
            and (char2 := self._maybe(self._ranges, ('0', '7'))) is not None
        ):
            _1 = _1.value
            char1 = char1.value
            char2 = char2.value

            # oct_char_action_2
            char2 = char2 if isinstance(char2, str) else ''
            string = ''.join((char1, char2))
            return Char(int(string, base=8))
        self._reset(_begin_pos)
        if (
            (_1 := self._expects("\\u")) is not None
            and (chars := self._rep(4, None, self._HexDigit)) is not None
        ):
            _1 = _1.value
            chars = chars.value

            # unicode_char_action
            string = ''.join(chars)
            return Char(int(string, base=16))
        self._reset(_begin_pos)
        if (
            self._lookahead(False, self._expectc, '\\')
            and (any := self._AnyChar__GEN()) is not None
        ):
            any = any.value

            # any_char_action
            return Char(ord(any))
        self._reset(_begin_pos)
        return None

    @_memoize
    def _Repetition(self):
        _begin_pos = self._mark()
        if (
            (_1 := self._expectc('{')) is not None
            and (grp := self._Repetition__GEN_1()) is not None
            and (_2 := self._expectc('}')) is not None
            and self._Spacing() is not None
        ):
            _1 = _1.value
            grp = grp.value
            _2 = _2.value

            # rep_action
            beg, end = grp if isinstance(grp, tuple) else (grp, None)
            return lambda item: Repetition(item, beg, end)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _Number(self):
        _begin_pos = self._mark()
        if ((chars := self._loop(True, self._ranges, ('0', '9'))) is not None):
            chars = chars.value

            # number_action
            string = ''.join(chars)
            return int(string)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _HexDigit(self):
        _begin_pos = self._mark()
        if ((char := self._ranges(('a', 'f'), ('A', 'F'), ('0', '9'))) is not None):
            char = char.value
            return Success(char)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _LEFTARROW(self):
        _begin_pos = self._mark()
        if (
            (_1 := self._expects("<-")) is not None
            and self._Spacing() is not None
        ):
            _1 = _1.value
            return Success(_1)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _SLASH(self):
        _begin_pos = self._mark()
        if (
            (_1 := self._expectc('/')) is not None
            and self._Spacing() is not None
        ):
            _1 = _1.value
            return Success(_1)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _AND(self):
        _begin_pos = self._mark()
        if (
            (_1 := self._expectc('&')) is not None
            and self._Spacing() is not None
        ):
            _1 = _1.value

            # and_action
            return And
        self._reset(_begin_pos)
        return None

    @_memoize
    def _NOT(self):
        _begin_pos = self._mark()
        if (
            (_1 := self._expectc('!')) is not None
            and self._Spacing() is not None
        ):
            _1 = _1.value

            # not_action
            return Not
        self._reset(_begin_pos)
        return None

    @_memoize
    def _QUESTION(self):
        _begin_pos = self._mark()
        if (
            (_1 := self._expectc('?')) is not None
            and self._Spacing() is not None
        ):
            _1 = _1.value

            # optional_action
            return ZeroOrOne
        self._reset(_begin_pos)
        return None

    @_memoize
    def _STAR(self):
        _begin_pos = self._mark()
        if (
            (_1 := self._expectc('*')) is not None
            and self._Spacing() is not None
        ):
            _1 = _1.value

            # zero_or_more_action
            return ZeroOrMore
        self._reset(_begin_pos)
        return None

    @_memoize
    def _PLUS(self):
        _begin_pos = self._mark()
        if (
            (_1 := self._expectc('+')) is not None
            and self._Spacing() is not None
        ):
            _1 = _1.value

            # one_or_more_action
            return OneOrMore
        self._reset(_begin_pos)
        return None

    @_memoize
    def _OPEN(self):
        _begin_pos = self._mark()
        if (
            (_1 := self._expectc('(')) is not None
            and self._Spacing() is not None
        ):
            _1 = _1.value
            return Success(_1)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _CLOSE(self):
        _begin_pos = self._mark()
        if (
            (_1 := self._expectc(')')) is not None
            and self._Spacing() is not None
        ):
            _1 = _1.value
            return Success(_1)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _DOT(self):
        _begin_pos = self._mark()
        if (
            (_1 := self._expectc('.')) is not None
            and self._Spacing() is not None
        ):
            _1 = _1.value

            # dot_action
            return AnyChar()
        self._reset(_begin_pos)
        return None

    @_memoize
    def _AT(self):
        _begin_pos = self._mark()
        if (
            (_1 := self._expectc('@')) is not None
            and self._Spacing() is not None
        ):
            _1 = _1.value
            return Success(_1)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _SEMI(self):
        _begin_pos = self._mark()
        if (
            (_1 := self._expectc(':')) is not None
            and self._Spacing() is not None
        ):
            _1 = _1.value
            return Success(_1)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _Spacing(self):
        _begin_pos = self._mark()
        if ((_1 := self._loop(False, self._Spacing__GEN_1)) is not None):
            _1 = _1.value
            return Success(_1)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _Comment(self):
        _begin_pos = self._mark()
        if (
            (_1 := self._expectc('#')) is not None
            and (_2 := self._loop(False, self._Comment__GEN_1)) is not None
            and (endofline := self._EndOfLine()) is not None
        ):
            _1 = _1.value
            _2 = _2.value
            endofline = endofline.value
            __tup = tuple(x for x in (_1, _2, endofline) if x is not None)
            return Success(__tup)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _Space(self):
        _begin_pos = self._mark()
        if ((_1 := self._expectc('\u0020')) is not None):
            _1 = _1.value
            return Success(_1)
        self._reset(_begin_pos)
        if ((_1 := self._expectc('\u0009')) is not None):
            _1 = _1.value
            return Success(_1)
        self._reset(_begin_pos)
        if ((endofline := self._EndOfLine()) is not None):
            endofline = endofline.value
            return Success(endofline)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _EndOfLine(self):
        _begin_pos = self._mark()
        if ((_1 := self._expects("\u000d\u000a")) is not None):
            _1 = _1.value
            return Success(_1)
        self._reset(_begin_pos)
        if ((_1 := self._expectc('\u000a')) is not None):
            _1 = _1.value
            return Success(_1)
        self._reset(_begin_pos)
        if ((_1 := self._expectc('\u000d')) is not None):
            _1 = _1.value
            return Success(_1)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _EndOfFile(self):
        _begin_pos = self._mark()
        if (self._lookahead(False, self._AnyChar__GEN)):
            return Success()
        self._reset(_begin_pos)
        return None

    @_memoize
    def _AnyChar__GEN(self):
        _begin_pos = self._mark()
        if ((_1 := self._expectc()) is not None):
            _1 = _1.value
            return Success(_1)
        self._reset(_begin_pos)
        return None

    @_memoize_lr
    def _Expression__GEN_1(self):
        _begin_pos = self._mark()
        if (
            self._SLASH() is not None
            and (sequence := self._Sequence()) is not None
        ):
            sequence = sequence.value
            return Success(sequence)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _Prefix__GEN_1(self):
        _begin_pos = self._mark()
        if ((_and := self._AND()) is not None):
            _and = _and.value
            return Success(_and)
        self._reset(_begin_pos)
        if ((_not := self._NOT()) is not None):
            _not = _not.value
            return Success(_not)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _Suffix__GEN_1(self):
        _begin_pos = self._mark()
        if ((question := self._QUESTION()) is not None):
            question = question.value
            return Success(question)
        self._reset(_begin_pos)
        if ((star := self._STAR()) is not None):
            star = star.value
            return Success(star)
        self._reset(_begin_pos)
        if ((plus := self._PLUS()) is not None):
            plus = plus.value
            return Success(plus)
        self._reset(_begin_pos)
        if ((repetition := self._Repetition()) is not None):
            repetition = repetition.value
            return Success(repetition)
        self._reset(_begin_pos)
        return None

    @_memoize_lr
    def _MetaRule__GEN_1(self):
        _begin_pos = self._mark()
        if ((nestedbody := self._NestedBody()) is not None):
            nestedbody = nestedbody.value
            return Success(nestedbody)
        self._reset(_begin_pos)
        if (
            self._lookahead(False, self._expectc, '}')
            and (_1 := self._AnyChar__GEN()) is not None
        ):
            _1 = _1.value
            return Success(_1)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _Literal__GEN_1(self):
        _begin_pos = self._mark()
        if (
            self._lookahead(False, self._ranges, ("'", "'"))
            and (char := self._Char()) is not None
        ):
            char = char.value
            return Success(char)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _Literal__GEN_2(self):
        _begin_pos = self._mark()
        if (
            self._lookahead(False, self._ranges, ('"', '"'))
            and (char := self._Char()) is not None
        ):
            char = char.value
            return Success(char)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _Class__GEN_1(self):
        _begin_pos = self._mark()
        if (
            self._lookahead(False, self._expectc, ']')
            and (range := self._Range()) is not None
        ):
            range = range.value
            return Success(range)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _Repetition__GEN_1(self):
        _begin_pos = self._mark()
        if (
            (number := self._Number()) is not None
            and self._expectc(',') is not None
            and (number1 := self._Number()) is not None
        ):
            number = number.value
            number1 = number1.value
            __tup = tuple(x for x in (number, number1) if x is not None)
            return Success(__tup)
        self._reset(_begin_pos)
        if ((number := self._Number()) is not None):
            number = number.value
            return Success(number)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _Spacing__GEN_1(self):
        _begin_pos = self._mark()
        if ((space := self._Space()) is not None):
            space = space.value
            return Success(space)
        self._reset(_begin_pos)
        if ((comment := self._Comment()) is not None):
            comment = comment.value
            return Success(comment)
        self._reset(_begin_pos)
        return None

    @_memoize
    def _Comment__GEN_1(self):
        _begin_pos = self._mark()
        if (
            self._lookahead(False, self._EndOfLine)
            and (_1 := self._AnyChar__GEN()) is not None
        ):
            _1 = _1.value
            return Success(_1)
        self._reset(_begin_pos)
        return None


if __name__ == '__main__':
    from argparse import ArgumentParser, FileType
    import sys

    argparser = ArgumentParser()
    argparser.add_argument('input_file', nargs='?',
                           type=FileType('r', encoding='UTF-8'),
                           default=sys.stdin)

    ns = argparser.parse_args()

    parser = Parser(ns.input_file)
    result = parser.parse()

    if result is not None:
        print(result)

    print("Parsing successful" if result else "Parsing failure")
    exit(not result)  # Unix-style: 0 is success

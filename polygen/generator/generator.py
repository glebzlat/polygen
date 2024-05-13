import sys

from io import StringIO
from pathlib import Path
from datetime import datetime
from typing import Optional, TextIO

from polygen.__version__ import __version__
from polygen.parsing import Parser as GrammarParser
from polygen.grammar.node import Grammar
from polygen.grammar.tree_modifier import (
    ExpandClass,
    ReplaceRep,
    CheckUndefRedef,
    SimplifyNestedExps,
    ReplaceNestedExps,
    CreateAnyCharRule,
    FindEntryRule,
    IgnoreRules,
    GenerateMetanames,
    SubstituteMetaRefs,
    TreeModifier,
    TreeModifierWarning
)

from polygen.backend.python import PythonGenerator
from .preprocessor import Preprocessor


class GeneratorError(Exception):
    pass


class Generator:
    def __init__(self, datefmt: Optional[str] = None):
        self.datefmt = datefmt or "%Y-%m-%d %I:%M %p"

    def _modify(self, grammar: Grammar, errstream) -> None:
        write_rules = [
            [SubstituteMetaRefs()],
            [CreateAnyCharRule()],
            [
                ExpandClass(),
                ReplaceRep(),
            ],
            [FindEntryRule(), IgnoreRules()],
            [SimplifyNestedExps(), ReplaceNestedExps()],
            [CheckUndefRedef()],
            [GenerateMetanames()],
        ]

        modifier = TreeModifier(write_rules)

        try:
            modifier.visit(grammar)

        except TreeModifierWarning as warn:
            warnings = warn.args
            for w in warnings:
                name = type(w).__name__
                nodes = w.args
                print(f"Warning {name}:")
                for n in nodes:
                    print(f"    {n}")

    def get_grammar(self, file, *, modified=False) -> Optional[Grammar]:
        parser = GrammarParser(file)

        grammar = parser.parse()
        if grammar is None:
            raise GeneratorError("Parser failure")

        if modified:
            self._modify(grammar, sys.stderr)

        return grammar

    def generate(self,
                 grammar_file: str | TextIO,
                 skeleton: str | Path,
                 output: str | Path):
        grammar = self.get_grammar(grammar_file, modified=True)

        stream = StringIO()
        gen = PythonGenerator(stream)
        gen.generate(grammar)
        stream.seek(0)

        directives = {
            "body": stream,
            "entry": grammar.entry.id.string,
            "version": __version__,
            "datetime": datetime.today().strftime(self.datefmt)
        }

        proc = Preprocessor(directives)
        proc.process(skeleton, output)

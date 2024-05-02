import re
import sys

from io import StringIO
from typing import TextIO


class PreprocessorError(Exception):
    pass


class Preprocessor:
    """Creates a source code from the skeleton file, substituting directives.

    Directives are words, wrapped by two percent symbols '%' like so:
    "%% directive %%". Preprocessor will match directive and replace it,
    preserving the prefix for _each_ line in the substitution, and also
    preserving the postfix at the end of the substitution.

    Preserving prefix means that if the directive is, e.g. indented or
    commented, then each line of the substituting text will also be
    indented or commented with the same symbols.

    But postfix is preserved once and placed at the end of the substituting
    text, not at the end of each line.

    Suppose that there is a directive `my_directive` with the replacement
    `Hello\nWorld`. Then the following line in the skeleton file:

    ```
    ### %% my_directive %% !
    ```

    will be transformed to:

    ```
    ### Hello
    ### World !
    ```

    Lines that do not contain valid directives, will be written without
    changes.
    """

    _DIRECTIVE_RE = re.compile(r'(.*)(?<!\\)%% *(\w+) *%%(.*)\Z',
                               flags=re.DOTALL)
    _NEWLINE_RE = re.compile(r'\A\n\r?\Z')

    def __init__(self, directives: dict[str, str | TextIO]):
        """Initialize Preprocessor.

        Arguments:
            directives: A mapping from the directive name to its substitution.
        """
        self.directives = directives

    def _insert(self,
                content: str | TextIO,
                ostream: TextIO,
                prefix: str,
                postfix: str) -> None:
        istream = StringIO(content) if isinstance(content, str) else content

        for line in istream:
            if self._NEWLINE_RE.match(line):
                ostream.write(line)
            else:
                ostream.write(prefix + line)
        ostream.write(postfix)

    def process(self,
                istream: str | TextIO,
                ostream: TextIO = sys.stdout) -> None:
        """Process input stream and write to output stream.

        Args:
            istream: Input stream.
            ostream: Output stream.

        Raises:
            PreprocessorError
        """
        istream = StringIO(istream) if isinstance(istream, str) else istream

        for line in istream:
            if m := self._DIRECTIVE_RE.match(line):
                prefix, directive, postfix = m.group(1, 2, 3)
                content = self.directives.get(directive)
                if content is None:
                    raise PreprocessorError
                self._insert(content, ostream, prefix, postfix)
            else:
                ostream.write(line)

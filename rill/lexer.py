from dataclasses import dataclass
from .tokens import Token, TokenType, KEYWORDS
from .ast_nodes import *


class LexError(Exception):
    def __init__(self, msg: str, line: int, col: int):
        super().__init__(f"Lex error at L{line}:C{col}: {msg}")
        self.line = line
        self.col = col


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: list[Token] = []

    def peek(self) -> str | None:
        if self.pos < len(self.source):
            return self.source[self.pos]
        return None

    def advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def match(self, expected: str) -> bool:
        if self.pos + len(expected) <= len(self.source):
            if self.source[self.pos : self.pos + len(expected)] == expected:
                for _ in expected:
                    self.advance()
                return True
        return False

    def add_token(self, type: TokenType, value=None):
        self.tokens.append(Token(type, value, self.line, self.col))

    def skip_whitespace(self):
        while self.pos < len(self.source) and self.source[self.pos] in " \t\r":
            self.advance()

    def skip_comment(self):
        if self.match("//"):
            while self.pos < len(self.source) and self.source[self.pos] != "\n":
                self.advance()
            return True
        return False

    def read_string(self) -> str:
        self.advance()  # opening "
        chars = []
        while self.pos < len(self.source) and self.source[self.pos] != '"':
            if self.source[self.pos] == "\\":
                self.advance()
                ch = self.advance()
                escape_map = {"n": "\n", "t": "\t", "\\": "\\", '"': '"'}
                chars.append(escape_map.get(ch, ch))
            else:
                chars.append(self.advance())
        if self.pos >= len(self.source):
            raise LexError("Unterminated string", self.line, self.col)
        self.advance()  # closing "
        return "".join(chars)

    def read_fstring(self) -> list[tuple[str, str | None]]:
        self.advance()  # opening "
        parts = []
        current = []
        depth = 0
        while self.pos < len(self.source) and (self.source[self.pos] != '"' or depth > 0):
            ch = self.source[self.pos]
            if ch == "\\":
                self.advance()
                esc = self.advance()
                escape_map = {"n": "\n", "t": "\t", "\\": "\\", '"': '"'}
                current.append(escape_map.get(esc, esc))
                continue
            if ch == "{" and depth == 0:
                parts.append(("".join(current), None))
                current = []
                self.advance()  # consume '{'
                expr_chars = []
                depth = 1
                while self.pos < len(self.source) and depth > 0:
                    c = self.source[self.pos]
                    if c == "{":
                        depth += 1
                    elif c == "}":
                        depth -= 1
                        if depth == 0:
                            self.advance()  # consume '}'
                            break
                    expr_chars.append(self.advance())
                parts.append((None, "".join(expr_chars)))
                continue
            current.append(self.advance())
        if self.pos >= len(self.source):
            raise LexError("Unterminated f-string", self.line, self.col)
        self.advance()  # closing "
        if current:
            parts.append(("".join(current), None))
        return parts

    def read_number(self) -> Token:
        start_col = self.col
        digits = []
        has_dot = False
        while self.pos < len(self.source) and (self.source[self.pos].isdigit() or self.source[self.pos] == "."):
            if self.source[self.pos] == ".":
                if has_dot:
                    break
                has_dot = True
            digits.append(self.advance())
        num_str = "".join(digits)
        if has_dot:
            return Token(TokenType.FLOAT, float(num_str), self.line, start_col)
        return Token(TokenType.INT, int(num_str), self.line, start_col)

    def read_ident(self) -> Token:
        start_col = self.col
        chars = []
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == "_"):
            chars.append(self.advance())
        word = "".join(chars)
        if word in ("true", "false"):
            return Token(TokenType.BOOL, word == "true", self.line, start_col)
        if word in KEYWORDS:
            return Token(KEYWORDS[word], word, self.line, start_col)
        return Token(TokenType.IDENT, word, self.line, start_col)

    def tokenize(self) -> list[Token]:
        while self.pos < len(self.source):
            self.skip_whitespace()
            if self.pos >= len(self.source):
                break

            if self.skip_comment():
                continue

            ch = self.peek()
            if ch is None:
                break

            start_col = self.col
            start_line = self.line

            # Newlines (significant in Rill)
            if ch == "\n":
                self.advance()
                # Collapse consecutive newlines
                if self.tokens and self.tokens[-1].type != TokenType.NEWLINE:
                    self.tokens.append(Token(TokenType.NEWLINE, "\\n", start_line, start_col))
                continue

            # F-strings
            if ch == 'f' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '"':
                self.advance()  # consume 'f'
                parts = self.read_fstring()
                self.tokens.append(Token(TokenType.FSTRING, parts, start_line, start_col))
                continue

            # Strings
            if ch == '"':
                s = self.read_string()
                self.tokens.append(Token(TokenType.STRING, s, start_line, start_col))
                continue

            # Numbers
            if ch.isdigit():
                self.tokens.append(self.read_number())
                continue

            # Identifiers and keywords
            if ch.isalpha() or ch == "_":
                self.tokens.append(self.read_ident())
                continue

            # Operators and delimiters
            self.advance()
            two_char = ch + (self.peek() or "")

            op_map = {
                "+": TokenType.PLUS,
                "-": TokenType.MINUS,
                "*": TokenType.STAR,
                "/": TokenType.SLASH,
                "%": TokenType.PERCENT,
                "(": TokenType.LPAREN,
                ")": TokenType.RPAREN,
                "{": TokenType.LBRACE,
                "}": TokenType.RBRACE,
                "[": TokenType.LBRACKET,
                "]": TokenType.RBRACKET,
                ",": TokenType.COMMA,
                ";": TokenType.SEMICOLON,
                ":": TokenType.COLON,
                ".": TokenType.DOT,
                "_": TokenType.UNDERSCORE,
            }

            two_char_ops = {
                "==": TokenType.EQ,
                "!=": TokenType.NEQ,
                "<=": TokenType.LTE,
                ">=": TokenType.GTE,
                "&&": TokenType.AND,
                "||": TokenType.OR,
                "|>": TokenType.PIPE,
                "->": TokenType.ARROW,
            }

            if two_char in two_char_ops:
                self.advance()
                self.tokens.append(Token(two_char_ops[two_char], two_char, start_line, start_col))
            elif ch == "=":
                self.tokens.append(Token(TokenType.ASSIGN, "=", start_line, start_col))
            elif ch == "<":
                self.tokens.append(Token(TokenType.LT, "<", start_line, start_col))
            elif ch == ">":
                self.tokens.append(Token(TokenType.GT, ">", start_line, start_col))
            elif ch == "!":
                self.tokens.append(Token(TokenType.NOT, "!", start_line, start_col))
            elif ch in op_map:
                self.tokens.append(Token(op_map[ch], ch, start_line, start_col))
            else:
                raise LexError(f"Unexpected character: {ch!r}", start_line, start_col)

        self.tokens.append(Token(TokenType.EOF, None, self.line, self.col))
        return self.tokens

from .tokens import Token, TokenType
from .ast_nodes import *


class ParseError(Exception):
    def __init__(self, msg: str, token: Token):
        super().__init__(f"Parse error at L{token.line}:C{token.col}: {msg}")
        self.token = token


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def expect(self, type: TokenType) -> Token:
        tok = self.peek()
        if tok.type != type:
            raise ParseError(f"Expected {type.name}, got {tok.type.name}", tok)
        return self.advance()

    def skip_newlines(self):
        while self.peek().type == TokenType.NEWLINE:
            self.advance()

    def parse(self) -> Program:
        stmts = []
        self.skip_newlines()
        while self.peek().type != TokenType.EOF:
            stmts.append(self.parse_stmt())
            self.skip_newlines()
        return Program(stmts)

    def parse_stmt(self) -> ASTNode:
        tok = self.peek()
        if tok.type == TokenType.LET:
            return self.parse_let()
        if tok.type == TokenType.FN:
            return self.parse_fn()
        if tok.type == TokenType.STRUCT:
            return self.parse_struct()
        if tok.type == TokenType.ENUM:
            return self.parse_enum()
        if tok.type == TokenType.IMPL:
            return self.parse_impl()
        if tok.type == TokenType.IDENT and self.pos + 1 < len(self.tokens):
            if self.tokens[self.pos + 1].type == TokenType.ASSIGN:
                name = self.advance().value
                self.advance()  # consume '='
                value = self.parse_expr()
                return AssignExpr(name, value, tok.line)
        return self.parse_expr()

    def parse_let(self) -> LetDecl:
        tok = self.advance()  # consume 'let'
        mutable = False
        if self.peek().type == TokenType.MUT:
            self.advance()
            mutable = True
        name_tok = self.expect(TokenType.IDENT)
        type_ann = None
        if self.peek().type == TokenType.COLON:
            self.advance()
            type_ann = self.parse_type()
        self.expect(TokenType.ASSIGN)
        value = self.parse_expr()
        return LetDecl(name_tok.value, type_ann, value, mutable, tok.line)

    def parse_fn(self) -> FnExpr:
        tok = self.advance()  # consume 'fn'
        self.expect(TokenType.LPAREN)
        params = []
        if self.peek().type != TokenType.RPAREN:
            while True:
                name = self.expect(TokenType.IDENT).value
                type_ann = None
                if self.peek().type == TokenType.COLON:
                    self.advance()
                    type_ann = self.parse_type()
                params.append((name, type_ann))
                if self.peek().type != TokenType.COMMA:
                    break
                self.advance()
        self.expect(TokenType.RPAREN)
        return_type = None
        if self.peek().type == TokenType.ARROW:
            self.advance()
            return_type = self.parse_type()
        body = self.parse_block()
        return FnExpr(params, return_type, body, tok.line)

    def parse_block(self) -> list[ASTNode]:
        self.expect(TokenType.LBRACE)
        stmts = []
        self.skip_newlines()
        while self.peek().type != TokenType.RBRACE:
            stmts.append(self.parse_stmt())
            self.skip_newlines()
        self.expect(TokenType.RBRACE)
        return stmts

    def parse_type(self) -> ASTNode:
        tok = self.peek()
        if tok.type == TokenType.IDENT:
            self.advance()
            return TypeName(tok.value, tok.line)
        if tok.type == TokenType.LPAREN:
            self.advance()
            types = [self.parse_type()]
            while self.peek().type == TokenType.COMMA:
                self.advance()
                types.append(self.parse_type())
            self.expect(TokenType.RPAREN)
            if len(types) == 1:
                return types[0]
            return TupleType(types, tok.line)
        if tok.type == TokenType.FN:
            return self.parse_fn_type()
        raise ParseError(f"Expected type, got {tok.type.name}", tok)

    def parse_fn_type(self) -> FnType:
        tok = self.advance()  # consume 'fn'
        self.expect(TokenType.LPAREN)
        params = []
        if self.peek().type != TokenType.RPAREN:
            params.append(self.parse_type())
            while self.peek().type == TokenType.COMMA:
                self.advance()
                params.append(self.parse_type())
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.ARROW)
        return_type = self.parse_type()
        return FnType(params, return_type, tok.line)

    def parse_expr(self) -> ASTNode:
        return self.parse_pipe()

    def parse_pipe(self) -> ASTNode:
        left = self.parse_or()
        while self.peek().type == TokenType.PIPE:
            self.advance()
            right = self.parse_or()
            left = PipeExpr(left, right, left.line)
        return left

    def parse_or(self) -> ASTNode:
        left = self.parse_and()
        while self.peek().type == TokenType.OR:
            op = self.advance()
            right = self.parse_and()
            left = BinaryOp("||", left, right, op.line)
        return left

    def parse_and(self) -> ASTNode:
        left = self.parse_comparison()
        while self.peek().type == TokenType.AND:
            op = self.advance()
            right = self.parse_comparison()
            left = BinaryOp("&&", left, right, op.line)
        return left

    def parse_comparison(self) -> ASTNode:
        left = self.parse_addition()
        while self.peek().type in (TokenType.EQ, TokenType.NEQ,
                                    TokenType.LT, TokenType.GT,
                                    TokenType.LTE, TokenType.GTE):
            op = self.advance()
            right = self.parse_addition()
            left = BinaryOp(op.value, left, right, op.line)
        return left

    def parse_addition(self) -> ASTNode:
        left = self.parse_multiplication()
        while self.peek().type in (TokenType.PLUS, TokenType.MINUS):
            op = self.advance()
            right = self.parse_multiplication()
            left = BinaryOp(op.value, left, right, op.line)
        return left

    def parse_multiplication(self) -> ASTNode:
        left = self.parse_unary()
        while self.peek().type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self.advance()
            right = self.parse_unary()
            left = BinaryOp(op.value, left, right, op.line)
        return left

    def parse_unary(self) -> ASTNode:
        tok = self.peek()
        if tok.type == TokenType.MINUS:
            self.advance()
            operand = self.parse_unary()
            return UnaryOp("-", operand, tok.line)
        if tok.type == TokenType.NOT:
            self.advance()
            operand = self.parse_unary()
            return UnaryOp("!", operand, tok.line)
        return self.parse_call()

    def parse_call(self) -> ASTNode:
        left = self.parse_primary()
        while True:
            if self.peek().type == TokenType.LPAREN:
                self.advance()
                args = []
                if self.peek().type != TokenType.RPAREN:
                    args.append(self.parse_expr())
                    while self.peek().type == TokenType.COMMA:
                        self.advance()
                        args.append(self.parse_expr())
                self.expect(TokenType.RPAREN)
                left = CallExpr(left, args, left.line)
            elif self.peek().type == TokenType.DOT:
                self.advance()
                attr = self.expect(TokenType.IDENT).value
                # Check if it's a method call: obj.method(args)
                if self.peek().type == TokenType.LPAREN:
                    self.advance()
                    args = []
                    if self.peek().type != TokenType.RPAREN:
                        args.append(self.parse_expr())
                        while self.peek().type == TokenType.COMMA:
                            self.advance()
                            args.append(self.parse_expr())
                    self.expect(TokenType.RPAREN)
                    left = MethodCall(left, attr, args, left.line)
                else:
                    left = DotExpr(left, attr, left.line)
            elif self.peek().type == TokenType.LBRACKET:
                self.advance()
                index = self.parse_expr()
                self.expect(TokenType.RBRACKET)
                left = IndexExpr(left, index, left.line)
            else:
                break
        return left

    def parse_primary(self) -> ASTNode:
        tok = self.peek()

        if tok.type == TokenType.INT:
            self.advance()
            return IntLit(tok.value, tok.line)
        if tok.type == TokenType.FLOAT:
            self.advance()
            return FloatLit(tok.value, tok.line)
        if tok.type == TokenType.STRING:
            self.advance()
            return StringLit(tok.value, tok.line)
        if tok.type == TokenType.BOOL:
            self.advance()
            return BoolLit(tok.value, tok.line)
        if tok.type == TokenType.IDENT:
            # Check for struct literal: TypeName { field: val, ... }
            if self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].type == TokenType.LBRACE:
                name = self.advance().value
                self.advance()  # consume '{'
                fields = []
                self.skip_newlines()
                while self.peek().type != TokenType.RBRACE:
                    field_name = self.expect(TokenType.IDENT).value
                    self.expect(TokenType.COLON)
                    value = self.parse_expr()
                    fields.append((field_name, value))
                    if self.peek().type == TokenType.COMMA:
                        self.advance()
                    self.skip_newlines()
                self.expect(TokenType.RBRACE)
                return StructLiteral(name, fields, tok.line)
            self.advance()
            return Ident(tok.value, tok.line)
        if tok.type == TokenType.LPAREN:
            self.advance()
            if self.peek().type == TokenType.RPAREN:
                self.advance()
                return UnitLit(tok.line)
            expr = self.parse_expr()
            if self.peek().type == TokenType.COMMA:
                # Tuple
                elements = [expr]
                while self.peek().type == TokenType.COMMA:
                    self.advance()
                    if self.peek().type == TokenType.RPAREN:
                        break
                    elements.append(self.parse_expr())
                self.expect(TokenType.RPAREN)
                # Return as a call to a tuple constructor (simplified: just return elements)
                return CallExpr(Ident("__tuple__", tok.line), elements, tok.line)
            self.expect(TokenType.RPAREN)
            return expr
        if tok.type == TokenType.LBRACKET:
            self.advance()
            elements = []
            if self.peek().type != TokenType.RBRACKET:
                elements.append(self.parse_expr())
                while self.peek().type == TokenType.COMMA:
                    self.advance()
                    if self.peek().type == TokenType.RBRACKET:
                        break
                    elements.append(self.parse_expr())
            self.expect(TokenType.RBRACKET)
            return CallExpr(Ident("__list__", tok.line), elements, tok.line)
        if tok.type == TokenType.FN:
            return self.parse_fn()
        if tok.type == TokenType.IF:
            return self.parse_if()
        if tok.type == TokenType.MATCH:
            return self.parse_match()
        if tok.type == TokenType.FOR:
            return self.parse_for()
        if tok.type == TokenType.WHILE:
            return self.parse_while()
        if tok.type == TokenType.BREAK:
            self.advance()
            value = None
            if self.peek().type not in (TokenType.NEWLINE, TokenType.RBRACE, TokenType.EOF):
                value = self.parse_expr()
            return BreakExpr(value, tok.line)
        if tok.type == TokenType.CONTINUE:
            self.advance()
            return ContinueExpr(tok.line)
        if tok.type == TokenType.RETURN:
            return self.parse_return()
        if tok.type == TokenType.UNDERSCORE:
            self.advance()
            return WildcardPattern(tok.line)
        if tok.type == TokenType.LBRACE:
            return Block(self.parse_block(), tok.line)
        if tok.type == TokenType.FSTRING:
            return self.parse_fstring()

        raise ParseError(f"Unexpected token {tok.type.name}: {tok.value!r}", tok)

    def parse_if(self) -> IfExpr:
        tok = self.advance()  # consume 'if'
        cond = self.parse_expr()
        then_body = self.parse_block()
        else_body = None
        if self.peek().type == TokenType.ELSE:
            self.advance()
            if self.peek().type == TokenType.IF:
                else_body = [self.parse_if()]
            else:
                else_body = self.parse_block()
        return IfExpr(cond, then_body, else_body, tok.line)

    def parse_match(self) -> MatchExpr:
        tok = self.advance()  # consume 'match'
        value = self.parse_expr()
        self.expect(TokenType.LBRACE)
        arms = []
        self.skip_newlines()
        while self.peek().type != TokenType.RBRACE:
            pattern = self.parse_pattern()
            self.expect(TokenType.ARROW)
            result = self.parse_expr()
            arms.append((pattern, result))
            if self.peek().type == TokenType.COMMA:
                self.advance()
            self.skip_newlines()
        self.expect(TokenType.RBRACE)
        return MatchExpr(value, arms, tok.line)

    def parse_pattern(self) -> ASTNode:
        tok = self.peek()
        if tok.type == TokenType.INT:
            self.advance()
            return IntPattern(tok.value, tok.line)
        if tok.type == TokenType.UNDERSCORE:
            self.advance()
            return WildcardPattern(tok.line)
        if tok.type == TokenType.IDENT:
            self.advance()
            p = IdentPattern(tok.value, tok.line)
            if self.peek().type == TokenType.IDENT and self.tokens[self.pos].value == "if":
                # Guard pattern: name if guard
                pass  # TODO: implement guards properly
            return p
        if tok.type == TokenType.LPAREN:
            self.advance()
            patterns = []
            if self.peek().type != TokenType.RPAREN:
                patterns.append(self.parse_pattern())
                while self.peek().type == TokenType.COMMA:
                    self.advance()
                    patterns.append(self.parse_pattern())
            self.expect(TokenType.RPAREN)
            return TuplePattern(patterns, tok.line)
        raise ParseError(f"Expected pattern, got {tok.type.name}", tok)

    def parse_for(self) -> ForExpr:
        tok = self.advance()  # consume 'for'
        var_name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.IN)
        iterable = self.parse_expr()
        body = self.parse_block()
        return ForExpr(var_name, iterable, body, tok.line)

    def parse_while(self) -> WhileExpr:
        tok = self.advance()  # consume 'while'
        cond = self.parse_expr()
        body = self.parse_block()
        return WhileExpr(cond, body, tok.line)

    def parse_fstring(self) -> FString:
        tok = self.advance()  # consume FSTRING token
        raw_parts = tok.value  # list of (literal_str, expr_str_or_None)
        parts = []
        for lit, expr in raw_parts:
            if expr is not None:
                # Parse the expression string
                from .lexer import Lexer
                expr_tokens = Lexer(expr).tokenize()
                expr_parser = Parser(expr_tokens)
                parsed_expr = expr_parser.parse_expr()
                parts.append((lit, parsed_expr))
            else:
                parts.append((lit, None))
        return FString(parts, tok.line)

    def parse_return(self) -> ReturnExpr:
        tok = self.advance()  # consume 'return'
        value = None
        if self.peek().type not in (TokenType.NEWLINE, TokenType.RBRACE, TokenType.EOF):
            value = self.parse_expr()
        return ReturnExpr(value, tok.line)

    def parse_struct(self) -> StructDef:
        tok = self.advance()  # consume 'struct'
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.LBRACE)
        fields = []
        self.skip_newlines()
        while self.peek().type != TokenType.RBRACE:
            field_name = self.expect(TokenType.IDENT).value
            type_ann = None
            if self.peek().type == TokenType.COLON:
                self.advance()
                type_ann = self.parse_type()
            fields.append((field_name, type_ann))
            if self.peek().type == TokenType.COMMA:
                self.advance()
            self.skip_newlines()
        self.expect(TokenType.RBRACE)
        return StructDef(name, fields, tok.line)

    def parse_enum(self) -> EnumDef:
        tok = self.advance()  # consume 'enum'
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.LBRACE)
        variants = []
        self.skip_newlines()
        while self.peek().type != TokenType.RBRACE:
            variant_name = self.expect(TokenType.IDENT).value
            fields = []
            if self.peek().type == TokenType.LPAREN:
                self.advance()
                if self.peek().type != TokenType.RPAREN:
                    fields.append(self.parse_type())
                    while self.peek().type == TokenType.COMMA:
                        self.advance()
                        fields.append(self.parse_type())
                self.expect(TokenType.RPAREN)
            variants.append((variant_name, fields))
            if self.peek().type == TokenType.COMMA:
                self.advance()
            self.skip_newlines()
        self.expect(TokenType.RBRACE)
        return EnumDef(name, variants, tok.line)

    def parse_impl(self) -> ImplBlock:
        tok = self.advance()  # consume 'impl'
        type_name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.LBRACE)
        methods = []
        self.skip_newlines()
        while self.peek().type != TokenType.RBRACE:
            self.expect(TokenType.FN)
            method_name = self.expect(TokenType.IDENT).value
            self.expect(TokenType.LPAREN)
            params = []
            if self.peek().type != TokenType.RPAREN:
                first = self.expect(TokenType.IDENT).value
                params.append((first, None))
                while self.peek().type == TokenType.COMMA:
                    self.advance()
                    pname = self.expect(TokenType.IDENT).value
                    params.append((pname, None))
            self.expect(TokenType.RPAREN)
            return_type = None
            if self.peek().type == TokenType.ARROW:
                self.advance()
                return_type = self.parse_type()
            body = self.parse_block()
            methods.append((method_name, FnExpr(params, body, return_type, tok.line)))
            self.skip_newlines()
        self.expect(TokenType.RBRACE)
        return ImplBlock(type_name, methods, tok.line)

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from .ast_nodes import *
from .opcodes import Op


class CompileError(Exception):
    def __init__(self, msg: str, line: int = 0):
        super().__init__(msg)
        self.line = line


@dataclass
class Chunk:
    bytecode: bytearray = field(default_factory=bytearray)
    constants: list[Any] = field(default_factory=list)
    lines: list[int] = field(default_factory=list)
    names: list[str] = field(default_factory=list)  # global name table

    def add_const(self, value: Any) -> int:
        self.constants.append(value)
        return len(self.constants) - 1

    def add_name(self, name: str) -> int:
        if name in self.names:
            return self.names.index(name)
        self.names.append(name)
        return len(self.names) - 1

    def emit(self, op: Op, line: int = 0):
        self.bytecode.append(op)
        self.lines.append(line)

    def emit_byte(self, byte: int, line: int = 0):
        self.bytecode.append(byte & 0xFF)
        self.lines.append(line)

    def emit_u16(self, value: int, line: int = 0):
        self.bytecode.append((value >> 8) & 0xFF)
        self.bytecode.append(value & 0xFF)
        self.lines.append(line)
        self.lines.append(line)

    def emit_op_u16(self, op: Op, value: int, line: int = 0):
        self.emit(op, line)
        self.emit_u16(value, line)

    def patch_jump(self, offset: int):
        # offset is where the 2-byte operand starts
        # ip after reading = offset + 2, target = len(bytecode)
        jump = len(self.bytecode) - offset - 2
        self.bytecode[offset] = (jump >> 8) & 0xFF
        self.bytecode[offset + 1] = jump & 0xFF


class Compiler:
    def __init__(self):
        self.chunk = Chunk()
        self.loop_stack: list[_Loop] = []
        self.scope_depth = 0

    def compile(self, program: Program) -> Chunk:
        for stmt in program.stmts:
            self._compile_stmt(stmt)
        self.chunk.emit(Op.HALT)
        return self.chunk

    def _compile_stmt(self, node: ASTNode):
        method = getattr(self, f"_compile_{type(node).__name__}", None)
        if method:
            method(node)
        else:
            self._compile_expr(node)
            self.chunk.emit(Op.POP, getattr(node, "line", 0))

    def _compile_expr(self, node: ASTNode):
        method = getattr(self, f"_compile_{type(node).__name__}", None)
        if method:
            method(node)
        else:
            raise CompileError(f"Cannot compile {type(node).__name__}")

    # ── Literals ─────────────────────────────────────────

    def _compile_IntLit(self, node: IntLit):
        idx = self.chunk.add_const(node.value)
        self.chunk.emit_op_u16(Op.LOAD_CONST, idx, node.line)

    def _compile_FloatLit(self, node: FloatLit):
        idx = self.chunk.add_const(node.value)
        self.chunk.emit_op_u16(Op.LOAD_CONST, idx, node.line)

    def _compile_StringLit(self, node: StringLit):
        idx = self.chunk.add_const(node.value)
        self.chunk.emit_op_u16(Op.LOAD_CONST, idx, node.line)

    def _compile_BoolLit(self, node: BoolLit):
        self.chunk.emit(Op.LOAD_TRUE if node.value else Op.LOAD_FALSE, node.line)

    def _compile_UnitLit(self, node: UnitLit):
        self.chunk.emit(Op.LOAD_NULL, node.line)

    def _compile_Ident(self, node: Ident):
        idx = self.chunk.add_name(node.name)
        self.chunk.emit_op_u16(Op.LOAD_GLOBAL, idx, node.line)

    # ── Operators ────────────────────────────────────────

    def _compile_BinaryOp(self, node: BinaryOp):
        self._compile_expr(node.left)
        self._compile_expr(node.right)
        ops = {
            "+": Op.ADD, "-": Op.SUB, "*": Op.MUL, "/": Op.DIV, "%": Op.MOD,
            "==": Op.EQ, "!=": Op.NEQ, "<": Op.LT, ">": Op.GT,
            "<=": Op.LTE, ">=": Op.GTE, "&&": Op.AND, "||": Op.OR,
        }
        if node.op in ops:
            self.chunk.emit(ops[node.op], node.line)
        else:
            raise CompileError(f"Unknown operator: {node.op}")

    def _compile_UnaryOp(self, node: UnaryOp):
        self._compile_expr(node.operand)
        if node.op == "-":
            self.chunk.emit(Op.NEG, node.line)
        elif node.op == "!":
            self.chunk.emit(Op.NOT, node.line)
        else:
            raise CompileError(f"Unknown unary operator: {node.op}")

    # ── Statements ───────────────────────────────────────

    def _compile_LetDecl(self, node: LetDecl):
        self._compile_expr(node.value)
        idx = self.chunk.add_name(node.name)
        self.chunk.emit_op_u16(Op.STORE_GLOBAL, idx, node.line)

    def _compile_AssignExpr(self, node: AssignExpr):
        self._compile_expr(node.value)
        idx = self.chunk.add_name(node.name)
        self.chunk.emit_op_u16(Op.STORE_GLOBAL, idx, node.line)

    def _compile_ReturnExpr(self, node: ReturnExpr):
        if node.value:
            self._compile_expr(node.value)
        else:
            self.chunk.emit(Op.LOAD_NULL, node.line)
        self.chunk.emit(Op.RETURN, node.line)

    # ── Control Flow ─────────────────────────────────────

    def _compile_IfExpr(self, node: IfExpr):
        self._compile_expr(node.cond)
        self.chunk.emit(Op.JUMP_IF_FALSE, node.line)
        jump_false = len(self.chunk.bytecode)  # points to 2-byte operand
        self.chunk.emit_u16(0, node.line)  # placeholder

        for stmt in node.then_body:
            self._compile_stmt(stmt)

        if node.else_body:
            self.chunk.emit(Op.JUMP, node.line)
            jump_over = len(self.chunk.bytecode)  # points to 2-byte operand
            self.chunk.emit_u16(0, node.line)
            self.chunk.patch_jump(jump_false)
            for stmt in node.else_body:
                self._compile_stmt(stmt)
            self.chunk.patch_jump(jump_over)
        else:
            self.chunk.patch_jump(jump_false)

    def _compile_WhileExpr(self, node: WhileExpr):
        loop_start = len(self.chunk.bytecode)
        self._compile_expr(node.cond)
        self.chunk.emit(Op.JUMP_IF_FALSE, node.line)
        exit_jump = len(self.chunk.bytecode)  # points to 2-byte operand
        self.chunk.emit_u16(0, node.line)

        self.loop_stack.append(_Loop(loop_start, len(self.chunk.bytecode)))

        for stmt in node.body:
            self._compile_stmt(stmt)

        # Jump back to start
        self.chunk.emit(Op.JUMP, node.line)
        # offset = loop_start - (operand_start + 2)
        jump_size = loop_start - len(self.chunk.bytecode) - 2
        self.chunk.emit_u16(jump_size & 0xFFFF, node.line)

        self.chunk.patch_jump(exit_jump)
        loop = self.loop_stack.pop()
        # Patch breaks
        for offset in loop.breaks:
            self.chunk.patch_jump(offset)

    def _compile_BreakExpr(self, node: BreakExpr):
        if not self.loop_stack:
            raise CompileError("break outside of loop", node.line)
        if node.value:
            self._compile_expr(node.value)
        else:
            self.chunk.emit(Op.LOAD_NULL, node.line)
        loop = self.loop_stack[-1]
        loop.breaks.append(len(self.chunk.bytecode))
        self.chunk.emit(Op.JUMP, node.line)
        self.chunk.emit_u16(0, node.line)  # placeholder

    def _compile_ContinueExpr(self, node: ContinueExpr):
        if not self.loop_stack:
            raise CompileError("continue outside of loop", node.line)
        loop = self.loop_stack[-1]
        jump_size = loop.start - len(self.chunk.bytecode) - 3
        self.chunk.emit(Op.JUMP, node.line)
        self.chunk.emit_u16(jump_size & 0xFFFF, node.line)

    def _compile_ForExpr(self, node: ForExpr):
        # Desugar: for i in iter { body } => let __iter = iter; let __idx = 0; while __idx < len(__iter) { let i = __iter[__idx]; __idx = __idx + 1; body }
        self._compile_expr(node.iterable)
        iter_idx = self.chunk.add_name("__iter")
        self.chunk.emit_op_u16(Op.STORE_GLOBAL, iter_idx, node.line)

        idx_idx = self.chunk.add_name("__idx")
        self.chunk.emit_op_u16(Op.LOAD_CONST, self.chunk.add_const(0), node.line)
        self.chunk.emit_op_u16(Op.STORE_GLOBAL, idx_idx, node.line)

        loop_start = len(self.chunk.bytecode)

        # __idx < len(__iter)
        self.chunk.emit_op_u16(Op.LOAD_GLOBAL, idx_idx, node.line)
        len_idx = self.chunk.add_name("len")
        self.chunk.emit_op_u16(Op.LOAD_GLOBAL, len_idx, node.line)
        self.chunk.emit_op_u16(Op.LOAD_GLOBAL, iter_idx, node.line)
        self.chunk.emit(Op.CALL, node.line)
        self.chunk.emit_byte(1, node.line)
        self.chunk.emit(Op.LT, node.line)

        self.chunk.emit(Op.JUMP_IF_FALSE, node.line)
        exit_jump = len(self.chunk.bytecode)  # points to 2-byte operand
        self.chunk.emit_u16(0, node.line)

        self.loop_stack.append(_Loop(loop_start, len(self.chunk.bytecode)))

        # let i = __iter[__idx]
        self.chunk.emit_op_u16(Op.LOAD_GLOBAL, iter_idx, node.line)
        self.chunk.emit_op_u16(Op.LOAD_GLOBAL, idx_idx, node.line)
        self.chunk.emit(Op.INDEX, node.line)
        var_idx = self.chunk.add_name(node.iter_var)
        self.chunk.emit_op_u16(Op.STORE_GLOBAL, var_idx, node.line)

        # __idx = __idx + 1
        self.chunk.emit_op_u16(Op.LOAD_GLOBAL, idx_idx, node.line)
        self.chunk.emit_op_u16(Op.LOAD_CONST, self.chunk.add_const(1), node.line)
        self.chunk.emit(Op.ADD, node.line)
        self.chunk.emit_op_u16(Op.STORE_GLOBAL, idx_idx, node.line)

        for stmt in node.body:
            self._compile_stmt(stmt)

        # Jump back
        back_jump = len(self.chunk.bytecode)
        self.chunk.emit(Op.JUMP, node.line)
        jump_size = loop_start - len(self.chunk.bytecode) - 2
        self.chunk.emit_u16(jump_size & 0xFFFF, node.line)

        self.chunk.patch_jump(exit_jump)
        loop = self.loop_stack.pop()
        for offset in loop.breaks:
            self.chunk.patch_jump(offset)

    # ── Functions ────────────────────────────────────────

    def _compile_FnExpr(self, node: FnExpr):
        # Emit as closure constant
        from .compiler import Compiler as FnCompiler
        fn_compiler = FnCompiler()
        for pname, _ in node.params:
            fn_compiler.chunk.add_name(pname)
        for stmt in node.body:
            fn_compiler._compile_stmt(stmt)
        fn_compiler.chunk.emit(Op.LOAD_NULL)
        fn_compiler.chunk.emit(Op.RETURN)
        fn_compiler.chunk.emit(Op.HALT)

        fn_chunk = fn_compiler.chunk
        idx = self.chunk.add_const(fn_chunk)
        self.chunk.emit_op_u16(Op.CLOSURE, idx, node.line)
        self.chunk.emit_byte(len(node.params), node.line)

    def _compile_CallExpr(self, node: CallExpr):
        self._compile_expr(node.callee)
        for arg in node.args:
            self._compile_expr(arg)
        self.chunk.emit(Op.CALL, node.line)
        self.chunk.emit_byte(len(node.args), node.line)

    # ── Collections ──────────────────────────────────────

    def _compile_IndexExpr(self, node: IndexExpr):
        self._compile_expr(node.obj)
        self._compile_expr(node.index)
        self.chunk.emit(Op.INDEX, node.line)

    # ── Pattern Matching (simplified) ────────────────────

    def _compile_MatchExpr(self, node: MatchExpr):
        self._compile_expr(node.value)
        self.chunk.emit(Op.DUP, node.line)
        jumps = []
        for pattern, result in node.arms:
            if isinstance(pattern, WildcardPattern):
                self.chunk.emit(Op.POP, node.line)
                self._compile_expr(result)
                jumps.append(len(self.chunk.bytecode))
                self.chunk.emit(Op.JUMP, node.line)
                self.chunk.emit_u16(0, node.line)
                continue
            if isinstance(pattern, IntPattern):
                self.chunk.emit(Op.DUP, node.line)
                idx = self.chunk.add_const(pattern.value)
                self.chunk.emit_op_u16(Op.LOAD_CONST, idx, node.line)
                self.chunk.emit(Op.EQ, node.line)
                jump_false = len(self.chunk.bytecode)
                self.chunk.emit(Op.JUMP_IF_FALSE, node.line)
                self.chunk.emit_u16(0, node.line)
                self.chunk.emit(Op.POP, node.line)
                self._compile_expr(result)
                jumps.append(len(self.chunk.bytecode))
                self.chunk.emit(Op.JUMP, node.line)
                self.chunk.emit_u16(0, node.line)
                self.chunk.patch_jump(jump_false)
                continue
        # Final: pop the value
        self.chunk.emit(Op.POP, node.line)
        for offset in jumps:
            self.chunk.patch_jump(offset)

    # ── FString (simplified: compile as string concat) ───

    def _compile_FString(self, node: FString):
        parts = []
        for lit, expr in node.parts:
            if lit:
                parts.append(StringLit(lit, node.line))
            if expr is not None:
                parts.append(expr)
        if not parts:
            idx = self.chunk.add_const("")
            self.chunk.emit_op_u16(Op.LOAD_CONST, idx, node.line)
            return
        self._compile_expr(parts[0])
        for part in parts[1:]:
            if isinstance(part, StringLit):
                self._compile_expr(part)
            else:
                # Need to convert to string — simplified: just concat
                self._compile_expr(part)
            self.chunk.emit(Op.ADD, node.line)

    # ── Block ────────────────────────────────────────────

    def _compile_Block(self, node: Block):
        for stmt in node.stmts:
            self._compile_stmt(stmt)


@dataclass
class _Loop:
    start: int
    continue_point: int
    breaks: list[int] = field(default_factory=list)

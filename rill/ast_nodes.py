from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


class ASTNode:
    pass


# ── Expressions ──────────────────────────────────────────

@dataclass
class IntLit(ASTNode):
    value: int
    line: int = 0


@dataclass
class FloatLit(ASTNode):
    value: float
    line: int = 0


@dataclass
class StringLit(ASTNode):
    value: str
    line: int = 0


@dataclass
class BoolLit(ASTNode):
    value: bool
    line: int = 0


@dataclass
class UnitLit(ASTNode):
    line: int = 0


@dataclass
class Ident(ASTNode):
    name: str
    line: int = 0


@dataclass
class BinaryOp(ASTNode):
    op: str
    left: ASTNode
    right: ASTNode
    line: int = 0


@dataclass
class UnaryOp(ASTNode):
    op: str
    operand: ASTNode
    line: int = 0


@dataclass
class CallExpr(ASTNode):
    callee: ASTNode
    args: list[ASTNode]
    line: int = 0


@dataclass
class PipeExpr(ASTNode):
    left: ASTNode
    right: ASTNode
    line: int = 0


@dataclass
class IndexExpr(ASTNode):
    obj: ASTNode
    index: ASTNode
    line: int = 0


@dataclass
class DotExpr(ASTNode):
    obj: ASTNode
    attr: str
    line: int = 0


# ── Statements ───────────────────────────────────────────

@dataclass
class LetDecl(ASTNode):
    name: str
    type_ann: ASTNode | None
    value: ASTNode
    mutable: bool = False
    line: int = 0


@dataclass
class FnExpr(ASTNode):
    params: list[tuple[str, ASTNode | None]]
    return_type: ASTNode | None
    body: list[ASTNode]
    line: int = 0


@dataclass
class IfExpr(ASTNode):
    cond: ASTNode
    then_body: list[ASTNode]
    else_body: list[ASTNode] | None
    line: int = 0


@dataclass
class MatchExpr(ASTNode):
    value: ASTNode
    arms: list[tuple[ASTNode, ASTNode]]
    line: int = 0


@dataclass
class ForExpr(ASTNode):
    iter_var: str
    iterable: ASTNode
    body: list[ASTNode]
    line: int = 0


@dataclass
class WhileExpr(ASTNode):
    cond: ASTNode
    body: list[ASTNode]
    line: int = 0


@dataclass
class BreakExpr(ASTNode):
    value: ASTNode | None
    line: int = 0


@dataclass
class ContinueExpr(ASTNode):
    line: int = 0


@dataclass
class FString(ASTNode):
    parts: list[tuple[str, ASTNode | None]]  # (literal_str, expr_or_None)
    line: int = 0


@dataclass
class AssignExpr(ASTNode):
    name: str
    value: ASTNode
    line: int = 0


@dataclass
class ReturnExpr(ASTNode):
    value: ASTNode | None
    line: int = 0


@dataclass
class Block(ASTNode):
    stmts: list[ASTNode]
    line: int = 0


@dataclass
class Program(ASTNode):
    stmts: list[ASTNode]


# ── Patterns ─────────────────────────────────────────────

@dataclass
class IntPattern(ASTNode):
    value: int
    line: int = 0


@dataclass
class IdentPattern(ASTNode):
    name: str
    line: int = 0


@dataclass
class WildcardPattern(ASTNode):
    line: int = 0


@dataclass
class TuplePattern(ASTNode):
    patterns: list[ASTNode]
    line: int = 0


@dataclass
class GuardPattern(ASTNode):
    pattern: ASTNode
    guard: ASTNode
    line: int = 0


# ── Type Annotations ─────────────────────────────────────

@dataclass
class TypeName(ASTNode):
    name: str
    line: int = 0


@dataclass
class FnType(ASTNode):
    params: list[ASTNode]
    return_type: ASTNode
    line: int = 0


@dataclass
class TupleType(ASTNode):
    types: list[ASTNode]
    line: int = 0

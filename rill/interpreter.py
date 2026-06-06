from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable
from .ast_nodes import *


class RillRuntimeError(Exception):
    def __init__(self, msg: str, line: int = 0):
        super().__init__(msg)
        self.line = line


class BreakSignal(Exception):
    def __init__(self, value=None):
        self.value = value


class ContinueSignal(Exception):
    pass


@dataclass
class RillFn:
    params: list[tuple[str, ASTNode | None]]
    body: list[ASTNode]
    closure: Environment
    name: str | None = None

    def __repr__(self):
        return f"<fn {self.name or 'lambda'}>"


class Environment:
    def __init__(self, parent: Environment | None = None):
        self.vars: dict[str, Any] = {}
        self.mutables: set[str] = set()
        self.parent = parent

    def get(self, name: str) -> Any:
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get(name)
        raise RillRuntimeError(f"Undefined variable: {name}")

    def set(self, name: str, value: Any, mutable: bool = False):
        self.vars[name] = value
        if mutable:
            self.mutables.add(name)

    def update(self, name: str, value: Any):
        if name in self.vars:
            if name not in self.mutables:
                raise RillRuntimeError(f"Cannot reassign immutable variable: {name}")
            self.vars[name] = value
            return
        if self.parent:
            self.parent.update(name, value)
            return
        raise RillRuntimeError(f"Undefined variable: {name}")

    def resolve(self, name: str) -> Environment:
        if name in self.vars:
            return self
        if self.parent:
            return self.parent.resolve(name)
        raise RillRuntimeError(f"Undefined variable: {name}")


@dataclass
class RillStruct:
    name: str
    fields: list[tuple[str, Any]]

    def __repr__(self):
        return f"<struct {self.name}>"


@dataclass
class RillEnum:
    name: str
    variants: dict[str, list[Any]]

    def __repr__(self):
        return f"<enum {self.name}>"


@dataclass
class RillVariant:
    enum_name: str
    variant_name: str
    data: tuple

    def __repr__(self):
        if self.data:
            return f"{self.variant_name}({', '.join(str(d) for d in self.data)})"
        return self.variant_name


@dataclass
class RillInstance:
    type_name: str
    fields: dict[str, Any]
    methods: dict[str, RillFn]

    def __repr__(self):
        fields_str = ", ".join(f"{k}: {v!r}" for k, v in self.fields.items())
        return f"{self.type_name} {{ {fields_str} }}"


class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        self._setup_builtins()

    def _setup_builtins(self):
        def _builtin(name, params, fn):
            self.global_env.set(name, RillFn(
                params=[(p, None) for p in params],
                body=[], closure=self.global_env, name=name,
            ))
            self._builtins[name] = fn

        self._builtins = {}

        _builtin("print", ["value"], lambda args: (print(self._to_rill_str(args[0])), None)[1])
        _builtin("println", ["value"], lambda args: (print(self._to_rill_str(args[0])), None)[1])
        _builtin("len", ["collection"], lambda args: len(args[0]))
        _builtin("range", ["start", "end"], lambda args: list(range(int(args[0]), int(args[1]))))
        _builtin("type", ["value"], lambda args: type(args[0]).__name__)
        _builtin("str", ["value"], lambda args: self._to_rill_str(args[0]))
        _builtin("int", ["value"], lambda args: int(args[0]))
        _builtin("float", ["value"], lambda args: float(args[0]))
        _builtin("bool", ["value"], lambda args: bool(args[0]))

        # List operations
        _builtin("map", ["list", "f"], lambda args: [self._apply_fn(args[1], [x]) for x in args[0]])
        _builtin("filter", ["list", "f"], lambda args: [x for x in args[0] if self._apply_fn(args[1], [x])])
        _builtin("fold", ["list", "f", "init"], lambda args: self._fold(args[0], args[1], args[2]))
        _builtin("reduce", ["list", "f"], lambda args: self._reduce(args[0], args[1]))
        _builtin("sort", ["list"], lambda args: sorted(args[0]))
        _builtin("sort_by", ["list", "f"], lambda args: sorted(args[0], key=lambda x: self._apply_fn(args[1], [x])))
        _builtin("reverse", ["list"], lambda args: list(reversed(args[0])))
        _builtin("flatten", ["list"], lambda args: [item for sublist in args[0] for item in sublist])
        _builtin("head", ["list"], lambda args: args[0][0] if args[0] else None)
        _builtin("tail", ["list"], lambda args: args[0][1:] if args[0] else [])
        _builtin("cons", ["elem", "list"], lambda args: [args[0]] + args[1])
        _builtin("append", ["list", "elem"], lambda args: args[0] + [args[1]])
        _builtin("sum", ["list"], lambda args: sum(args[0]))
        _builtin("min", ["list"], lambda args: min(args[0]))
        _builtin("max", ["list"], lambda args: max(args[0]))
        _builtin("any", ["list"], lambda args: any(args[0]))
        _builtin("all", ["list"], lambda args: all(args[0]))
        _builtin("zip", ["a", "b"], lambda args: list(zip(args[0], args[1])))
        _builtin("enumerate", ["list"], lambda args: list(enumerate(args[0])))
        _builtin("contains", ["list", "elem"], lambda args: args[1] in args[0])
        _builtin("index_of", ["list", "elem"], lambda args: args[0].index(args[1]) if args[1] in args[0] else -1)
        _builtin("unique", ["list"], lambda args: list(dict.fromkeys(args[0])))
        _builtin("take", ["list", "n"], lambda args: args[0][:args[1]])
        _builtin("drop", ["list", "n"], lambda args: args[0][args[1]:])
        _builtin("chunks", ["list", "size"], lambda args: [args[0][i:i+args[1]] for i in range(0, len(args[0]), args[1])])

        # String operations
        _builtin("split", ["s", "delim"], lambda args: args[0].split(args[1]))
        _builtin("join", ["list", "sep"], lambda args: args[1].join(args[0]))
        _builtin("str_contains", ["s", "sub"], lambda args: args[1] in args[0])
        _builtin("replace", ["s", "old", "new"], lambda args: args[0].replace(args[1], args[2]))
        _builtin("trim", ["s"], lambda args: args[0].strip())
        _builtin("upper", ["s"], lambda args: args[0].upper())
        _builtin("lower", ["s"], lambda args: args[0].lower())
        _builtin("chars", ["s"], lambda args: list(args[0]))
        _builtin("starts_with", ["s", "prefix"], lambda args: args[0].startswith(args[1]))
        _builtin("ends_with", ["s", "suffix"], lambda args: args[0].endswith(args[1]))
        _builtin("repeat", ["s", "n"], lambda args: args[0] * int(args[1]))
        _builtin("reverse_str", ["s"], lambda args: args[0][::-1])

        # IO
        _builtin("read_file", ["path"], lambda args: open(args[0], "r", encoding="utf-8").read())
        _builtin("write_file", ["path", "content"], lambda args: open(args[0], "w", encoding="utf-8").write(args[1]) or None)
        _builtin("input", [], lambda args: input())
        _builtin("input", ["prompt"], lambda args: input(self._to_rill_str(args[0])))

        # Math
        _builtin("abs", ["x"], lambda args: abs(args[0]))
        _builtin("sqrt", ["x"], lambda args: args[0] ** 0.5)
        _builtin("pow", ["base", "exp"], lambda args: args[0] ** args[1])
        _builtin("floor", ["x"], lambda args: int(args[0]))
        _builtin("ceil", ["x"], lambda args: -int(-args[0]))
        _builtin("round", ["x"], lambda args: round(args[0]))

        # Internal constructors
        self.global_env.set("__tuple__", RillFn(
            params=[("*args", None)], body=[], closure=self.global_env, name="__tuple__",
        ))
        self.global_env.set("__list__", RillFn(
            params=[("*args", None)], body=[], closure=self.global_env, name="__list__",
        ))

    def _apply_fn(self, fn, args):
        if isinstance(fn, RillFn):
            fn_env = Environment(fn.closure)
            for (pname, _), arg in zip(fn.params, args):
                fn_env.set(pname, arg)
            result = None
            for stmt in fn.body:
                result = self.exec_node(stmt, fn_env)
            return result
        if callable(fn):
            return fn(args)
        raise RillRuntimeError(f"Cannot call non-function: {type(fn).__name__}")

    def _fold(self, lst, fn, init):
        acc = init
        for item in lst:
            acc = self._apply_fn(fn, [acc, item])
        return acc

    def _reduce(self, lst, fn):
        if not lst:
            raise RillRuntimeError("reduce of empty list")
        acc = lst[0]
        for item in lst[1:]:
            acc = self._apply_fn(fn, [acc, item])
        return acc

    def run(self, program: Program) -> Any:
        result = None
        for stmt in program.stmts:
            result = self.exec_node(stmt, self.global_env)
        return result

    def exec_node(self, node: ASTNode, env: Environment) -> Any:
        # Dispatch based on node type
        method_name = f"_exec_{type(node).__name__}"
        method = getattr(self, method_name, None)
        if method:
            return method(node, env)
        raise RillRuntimeError(
            f"Unknown node type: {type(node).__name__}",
            getattr(node, "line", 0),
        )

    # ── Literals ─────────────────────────────────────────

    def _exec_IntLit(self, node: IntLit, env: Environment) -> int:
        return node.value

    def _exec_FloatLit(self, node: FloatLit, env: Environment) -> float:
        return node.value

    def _exec_StringLit(self, node: StringLit, env: Environment) -> str:
        return node.value

    def _exec_BoolLit(self, node: BoolLit, env: Environment) -> bool:
        return node.value

    def _exec_UnitLit(self, node: UnitLit, env: Environment) -> None:
        return None

    def _exec_Ident(self, node: Ident, env: Environment) -> Any:
        return env.get(node.name)

    # ── Operators ────────────────────────────────────────

    def _exec_BinaryOp(self, node: BinaryOp, env: Environment) -> Any:
        left = self.exec_node(node.left, env)
        right = self.exec_node(node.right, env)

        op = node.op
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            if right == 0:
                raise RillRuntimeError("Division by zero", node.line)
            if isinstance(left, float) or isinstance(right, float):
                return left / right
            return left // right
        if op == "%":
            return left % right
        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        if op == "<":
            return left < right
        if op == ">":
            return left > right
        if op == "<=":
            return left <= right
        if op == ">=":
            return left >= right
        if op == "&&":
            return left and right
        if op == "||":
            return left or right
        raise RillRuntimeError(f"Unknown operator: {op}", node.line)

    def _exec_UnaryOp(self, node: UnaryOp, env: Environment) -> Any:
        operand = self.exec_node(node.operand, env)
        if node.op == "-":
            return -operand
        if node.op == "!":
            return not operand
        raise RillRuntimeError(f"Unknown unary operator: {node.op}", node.line)

    # ── Expressions ──────────────────────────────────────

    def _exec_CallExpr(self, node: CallExpr, env: Environment) -> Any:
        callee = self.exec_node(node.callee, env)
        args = [self.exec_node(a, env) for a in node.args]

        if isinstance(callee, RillVariant):
            return RillVariant(callee.enum_name, callee.variant_name, tuple(args))

        if isinstance(callee, RillFn):
            # Handle builtins via dispatch dict
            if callee.name in self._builtins:
                return self._builtins[callee.name](args)
            if callee.name == "__tuple__":
                return tuple(args)
            if callee.name == "__list__":
                return list(args)

            # Check arity
            if len(args) != len(callee.params):
                raise RillRuntimeError(
                    f"{callee.name or 'fn'} expected {len(callee.params)} args, got {len(args)}",
                    node.line,
                )

            # Create new scope with closure
            fn_env = Environment(callee.closure)
            for (param_name, _), arg in zip(callee.params, args):
                fn_env.set(param_name, arg)

            # Execute body
            result = None
            for stmt in callee.body:
                result = self.exec_node(stmt, fn_env)
                if isinstance(stmt, ReturnExpr):
                    break
            return result

        raise RillRuntimeError(f"Cannot call non-function: {type(callee).__name__}", node.line)

    def _exec_PipeExpr(self, node: PipeExpr, env: Environment) -> Any:
        value = self.exec_node(node.left, env)
        func = self.exec_node(node.right, env)

        if isinstance(func, RillFn):
            return self._exec_CallExpr(
                CallExpr(node.right, [node.left], node.line), env
            )
        if callable(func):
            return func(value)
        raise RillRuntimeError(f"Cannot pipe into non-function", node.line)

    def _exec_DotExpr(self, node: DotExpr, env: Environment) -> Any:
        obj = self.exec_node(node.obj, env)
        if isinstance(obj, RillEnum):
            if node.attr not in obj.variants:
                raise RillRuntimeError(f"Variant '{node.attr}' not found on enum {obj.name}", node.line)
            return RillVariant(obj.name, node.attr, ())
        if isinstance(obj, RillInstance):
            if node.attr not in obj.fields:
                raise RillRuntimeError(f"Field '{node.attr}' not found on {obj.type_name}", node.line)
            return obj.fields[node.attr]
        if isinstance(obj, dict):
            if node.attr not in obj:
                raise RillRuntimeError(f"Key not found: {node.attr}", node.line)
            return obj[node.attr]
        raise RillRuntimeError(
            f"Cannot access attribute '{node.attr}' on {type(obj).__name__}", node.line
        )

    def _exec_IndexExpr(self, node: IndexExpr, env: Environment) -> Any:
        obj = self.exec_node(node.obj, env)
        idx = self.exec_node(node.index, env)
        if isinstance(obj, (list, tuple)):
            if isinstance(idx, int):
                if idx < 0 or idx >= len(obj):
                    raise RillRuntimeError(f"Index out of bounds: {idx}", node.line)
                return obj[idx]
        if isinstance(obj, str):
            if isinstance(idx, int):
                return obj[idx]
        raise RillRuntimeError(
            f"Cannot index into {type(obj).__name__}", node.line
        )

    # ── Statements ───────────────────────────────────────

    def _exec_LetDecl(self, node: LetDecl, env: Environment) -> None:
        value = self.exec_node(node.value, env)
        env.set(node.name, value, node.mutable)
        return value

    def _exec_AssignExpr(self, node: AssignExpr, env: Environment) -> Any:
        value = self.exec_node(node.value, env)
        env.update(node.name, value)
        return value

    def _exec_FnExpr(self, node: FnExpr, env: Environment) -> RillFn:
        return RillFn(
            params=node.params,
            body=node.body,
            closure=env,
            name=None,
        )

    def _exec_IfExpr(self, node: IfExpr, env: Environment) -> Any:
        cond = self.exec_node(node.cond, env)
        if cond:
            result = None
            for stmt in node.then_body:
                result = self.exec_node(stmt, env)
            return result
        elif node.else_body:
            result = None
            for stmt in node.else_body:
                result = self.exec_node(stmt, env)
            return result
        return None

    def _exec_MatchExpr(self, node: MatchExpr, env: Environment) -> Any:
        value = self.exec_node(node.value, env)
        for pattern, result in node.arms:
            match_env = Environment(env)
            if self._match_pattern(pattern, value, match_env):
                return self.exec_node(result, match_env)
        raise RillRuntimeError(f"No matching pattern for value: {value}", node.line)

    def _exec_ForExpr(self, node: ForExpr, env: Environment) -> Any:
        iterable = self.exec_node(node.iterable, env)
        result = None
        for item in iterable:
            loop_env = Environment(env)
            loop_env.set(node.iter_var, item)
            try:
                for stmt in node.body:
                    result = self.exec_node(stmt, loop_env)
            except BreakSignal as e:
                result = e.value
                break
            except ContinueSignal:
                continue
        return result

    def _exec_WhileExpr(self, node: WhileExpr, env: Environment) -> Any:
        result = None
        while self.exec_node(node.cond, env):
            try:
                for stmt in node.body:
                    result = self.exec_node(stmt, env)
            except BreakSignal as e:
                result = e.value
                break
            except ContinueSignal:
                continue
        return result

    def _exec_BreakExpr(self, node: BreakExpr, env: Environment) -> Any:
        value = None
        if node.value:
            value = self.exec_node(node.value, env)
        raise BreakSignal(value)

    def _exec_ContinueExpr(self, node: ContinueExpr, env: Environment) -> Any:
        raise ContinueSignal()

    def _exec_FString(self, node: FString, env: Environment) -> str:
        parts = []
        for lit, expr in node.parts:
            if lit:
                parts.append(lit)
            if expr is not None:
                val = self.exec_node(expr, env)
                parts.append(self._to_rill_str(val))
        return "".join(parts)

    def _exec_StructDef(self, node: StructDef, env: Environment) -> None:
        env.set(node.name, RillStruct(node.name, node.fields))

    def _exec_EnumDef(self, node: EnumDef, env: Environment) -> None:
        variants = {}
        for vname, vfields in node.variants:
            variants[vname] = vfields
        env.set(node.name, RillEnum(node.name, variants))

    def _exec_ImplBlock(self, node: ImplBlock, env: Environment) -> None:
        struct = env.get(node.type_name)
        if not isinstance(struct, RillStruct):
            raise RillRuntimeError(f"Cannot impl non-struct type: {node.type_name}", node.line)
        methods = {}
        for mname, mfn in node.methods:
            methods[mname] = RillFn(
                params=mfn.params,
                body=mfn.body,
                closure=env,
                name=mname,
            )
        env.set(f"{node.type_name}_methods", methods)

    def _exec_StructLiteral(self, node: StructLiteral, env: Environment) -> RillInstance:
        struct = env.get(node.name)
        if not isinstance(struct, RillStruct):
            raise RillRuntimeError(f"{node.name} is not a struct", node.line)
        fields = {}
        for fname, fval in node.fields:
            fields[fname] = self.exec_node(fval, env)
        methods_key = f"{node.name}_methods"
        methods = {}
        try:
            m = env.get(methods_key)
            if m:
                methods = m
        except RillRuntimeError:
            pass
        return RillInstance(node.name, fields, methods)

    def _exec_MethodCall(self, node: MethodCall, env: Environment) -> Any:
        obj = self.exec_node(node.obj, env)
        args = [self.exec_node(a, env) for a in node.args]
        # Enum variant construction: Color.Red(3.14)
        if isinstance(obj, RillEnum):
            if node.method not in obj.variants:
                raise RillRuntimeError(f"Variant '{node.method}' not found on enum {obj.name}", node.line)
            return RillVariant(obj.name, node.method, tuple(args))
        # Struct static method: Player.new("Hero")
        if isinstance(obj, RillStruct):
            methods_key = f"{obj.name}_methods"
            methods = {}
            try:
                m = env.get(methods_key)
                if m:
                    methods = m
            except RillRuntimeError:
                pass
            if node.method not in methods:
                raise RillRuntimeError(f"Method '{node.method}' not found on struct {obj.name}", node.line)
            method = methods[node.method]
            method_env = Environment(method.closure)
            for (pname, _), arg in zip(method.params, args):
                method_env.set(pname, arg)
            result = None
            for stmt in method.body:
                result = self.exec_node(stmt, method_env)
                if isinstance(stmt, ReturnExpr):
                    break
            return result
        if not isinstance(obj, RillInstance):
            raise RillRuntimeError(f"Cannot call method on non-instance: {type(obj).__name__}", node.line)
        if node.method not in obj.methods:
            raise RillRuntimeError(f"Method '{node.method}' not found on {obj.type_name}", node.line)
        method = obj.methods[node.method]
        # Create method env with self bound
        method_env = Environment(method.closure)
        method_env.set("self", obj)
        for (pname, _), arg in zip(method.params[1:], args):  # skip 'self' param
            method_env.set(pname, arg)
        result = None
        for stmt in method.body:
            result = self.exec_node(stmt, method_env)
            if isinstance(stmt, ReturnExpr):
                break
        return result

    def _exec_ReturnExpr(self, node: ReturnExpr, env: Environment) -> Any:
        if node.value:
            return self.exec_node(node.value, env)
        return None

    def _exec_Block(self, node: Block, env: Environment) -> Any:
        block_env = Environment(env)
        result = None
        for stmt in node.stmts:
            result = self.exec_node(stmt, block_env)
        return result

    # ── Pattern Matching ─────────────────────────────────

    def _match_pattern(self, pattern: ASTNode, value: Any, env: Environment) -> bool:
        if isinstance(pattern, IntPattern):
            return isinstance(value, int) and value == pattern.value
        if isinstance(pattern, IdentPattern):
            env.set(pattern.name, value)
            return True
        if isinstance(pattern, WildcardPattern):
            return True
        if isinstance(pattern, TuplePattern):
            if not isinstance(value, (tuple, list)):
                if isinstance(value, tuple):
                    value = value
                else:
                    return False
            if len(pattern.patterns) != len(value):
                return False
            for p, v in zip(pattern.patterns, value):
                if not self._match_pattern(p, v, env):
                    return False
            return True
        if isinstance(pattern, BoolLit):
            return value == pattern.value
        if isinstance(pattern, StringLit):
            return value == pattern.value
        return False

    # ── Helpers ──────────────────────────────────────────

    def _to_rill_str(self, value: Any) -> str:
        if value is None:
            return "()"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            return str(value)
        if isinstance(value, str):
            return value
        if isinstance(value, tuple):
            inner = ", ".join(self._to_rill_str(v) for v in value)
            return f"({inner})"
        if isinstance(value, list):
            inner = ", ".join(self._to_rill_str(v) for v in value)
            return f"[{inner}]"
        if isinstance(value, RillFn):
            return repr(value)
        if isinstance(value, RillInstance):
            fields = ", ".join(f"{k}: {self._to_rill_str(v)}" for k, v in value.fields.items())
            return f"{value.type_name} {{ {fields} }}"
        if isinstance(value, RillVariant):
            return repr(value)
        return str(value)

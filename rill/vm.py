from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from .opcodes import Op
from .compiler import Chunk


class VMError(Exception):
    def __init__(self, msg: str, line: int = 0):
        super().__init__(msg)
        self.line = line


@dataclass
class VMFunction:
    chunk: Chunk
    arity: int = 0
    name: str = "<fn>"


@dataclass
class VMClosure:
    fn: VMFunction
    upvalues: list[Any] = field(default_factory=list)


@dataclass
class _Frame:
    chunk: Chunk
    ip: int = 0


class VM:
    def __init__(self):
        self.stack: list[Any] = []
        self.globals: dict[str, Any] = {}
        self.ip = 0
        self.chunk: Chunk | None = None
        self.frames: list[_Frame] = []
        self._setup_builtins()

    def _setup_builtins(self):
        def _mk(name, fn):
            self.globals[name] = VMFunction(Chunk(), arity=0, name=name)
            self.globals[name]._native = fn

        def _print(args):
            val = args[0]
            if val is None:
                print("()")
            elif isinstance(val, bool):
                print("true" if val else "false")
            elif isinstance(val, list):
                inner = ", ".join(self._to_str(v) for v in val)
                print(f"[{inner}]")
            elif isinstance(val, tuple):
                inner = ", ".join(self._to_str(v) for v in val)
                print(f"({inner})")
            else:
                print(val)
            return None

        def _len(args):
            return len(args[0])

        def _range(args):
            return list(range(int(args[0]), int(args[1])))

        def _map(args):
            lst, fn = args[0], args[1]
            return [self._call_func(fn, [x]) for x in lst]

        def _filter(args):
            lst, fn = args[0], args[1]
            return [x for x in lst if self._call_func(fn, [x])]

        def _fold(args):
            lst, fn, init = args[0], args[1], args[2]
            acc = init
            for item in lst:
                acc = self._call_func(fn, [acc, item])
            return acc

        def _sort(args):
            return sorted(args[0])

        def _reverse(args):
            return list(reversed(args[0]))

        def _sum(args):
            return sum(args[0])

        def _head(args):
            return args[0][0] if args[0] else None

        def _tail(args):
            return args[0][1:] if args[0] else []

        def _cons(args):
            return [args[0]] + args[1]

        def _contains(args):
            return args[1] in args[0]

        def _unique(args):
            return list(dict.fromkeys(args[0]))

        def _abs(args):
            return abs(args[0])

        def _sqrt(args):
            return args[0] ** 0.5

        def _pow(args):
            return args[0] ** args[1]

        def _floor(args):
            return int(args[0])

        def _round_val(args):
            return round(args[0])

        def _split(args):
            return args[0].split(args[1])

        def _join(args):
            return args[1].join(args[0])

        def _upper(args):
            return args[0].upper()

        def _lower(args):
            return args[0].lower()

        def _trim(args):
            return args[0].strip()

        def _str(args):
            return self._to_str(args[0])

        def _int(args):
            return int(args[0])

        def _float(args):
            return float(args[0])

        def _bool_val(args):
            return bool(args[0])

        def _type_name(args):
            return type(args[0]).__name__

        def _input_val(args):
            if args:
                return input(self._to_str(args[0]))
            return input()

        def _read_file(args):
            with open(args[0], "r", encoding="utf-8") as f:
                return f.read()

        def _write_file(args):
            with open(args[0], "w", encoding="utf-8") as f:
                f.write(args[1])
            return None

        builtins = {
            "print": (1, _print), "println": (1, _print),
            "len": (1, _len), "range": (2, _range),
            "map": (2, _map), "filter": (2, _filter),
            "fold": (3, _fold), "sort": (1, _sort),
            "reverse": (1, _reverse), "sum": (1, _sum),
            "head": (1, _head), "tail": (1, _tail),
            "cons": (2, _cons), "contains": (2, _contains),
            "unique": (1, _unique), "abs": (1, _abs),
            "sqrt": (1, _sqrt), "pow": (2, _pow),
            "floor": (1, _floor), "round": (1, _round_val),
            "split": (2, _split), "join": (2, _join),
            "upper": (1, _upper), "lower": (1, _lower),
            "trim": (1, _trim), "str": (1, _str),
            "int": (1, _int), "float": (1, _float),
            "bool": (1, _bool_val), "type": (1, _type_name),
            "input": (-1, _input_val),
            "read_file": (1, _read_file),
            "write_file": (2, _write_file),
        }
        for name, (arity, fn) in builtins.items():
            self.globals[name] = ("builtin", fn, arity)

    def run(self, chunk: Chunk) -> Any:
        self.chunk = chunk
        self.ip = 0
        self.frames = [_Frame(chunk, 0)]
        return self._run()

    def _run(self) -> Any:
        while self.ip < len(self.chunk.bytecode):
            op = self.chunk.bytecode[self.ip]
            self.ip += 1

            if op == Op.HALT:
                break

            elif op == Op.LOAD_CONST:
                const_idx = (self.chunk.bytecode[self.ip] << 8) | self.chunk.bytecode[self.ip + 1]
                self.ip += 2
                self.stack.append(self.chunk.constants[const_idx])

            elif op == Op.LOAD_TRUE:
                self.stack.append(True)
            elif op == Op.LOAD_FALSE:
                self.stack.append(False)
            elif op == Op.LOAD_NULL:
                self.stack.append(None)

            elif op == Op.LOAD_GLOBAL:
                name_idx = (self.chunk.bytecode[self.ip] << 8) | self.chunk.bytecode[self.ip + 1]
                self.ip += 2
                name = self.chunk.names[name_idx]
                if name in self.globals:
                    self.stack.append(self.globals[name])
                else:
                    raise VMError(f"Undefined variable: {name}")

            elif op == Op.STORE_GLOBAL:
                name_idx = (self.chunk.bytecode[self.ip] << 8) | self.chunk.bytecode[self.ip + 1]
                self.ip += 2
                name = self.chunk.names[name_idx]
                self.globals[name] = self.stack[-1]

            elif op == Op.POP:
                self.stack.pop()

            elif op == Op.DUP:
                self.stack.append(self.stack[-1])

            elif op == Op.ADD:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a + b)
            elif op == Op.SUB:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a - b)
            elif op == Op.MUL:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a * b)
            elif op == Op.DIV:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a / b if isinstance(a, float) or isinstance(b, float) else a // b)
            elif op == Op.MOD:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a % b)
            elif op == Op.NEG:
                self.stack.append(-self.stack.pop())
            elif op == Op.NOT:
                self.stack.append(not self.stack.pop())

            elif op == Op.EQ:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a == b)
            elif op == Op.NEQ:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a != b)
            elif op == Op.LT:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a < b)
            elif op == Op.GT:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a > b)
            elif op == Op.LTE:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a <= b)
            elif op == Op.GTE:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a >= b)

            elif op == Op.AND:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a and b)
            elif op == Op.OR:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a or b)

            elif op == Op.JUMP:
                raw = (self.chunk.bytecode[self.ip] << 8) | self.chunk.bytecode[self.ip + 1]
                self.ip += 2
                offset = raw - 0x10000 if raw >= 0x8000 else raw
                self.ip += offset

            elif op == Op.JUMP_IF_FALSE:
                raw = (self.chunk.bytecode[self.ip] << 8) | self.chunk.bytecode[self.ip + 1]
                self.ip += 2
                offset = raw - 0x10000 if raw >= 0x8000 else raw
                if not self.stack[-1]:
                    self.ip += offset

            elif op == Op.JUMP_IF_TRUE:
                raw = (self.chunk.bytecode[self.ip] << 8) | self.chunk.bytecode[self.ip + 1]
                self.ip += 2
                offset = raw - 0x10000 if raw >= 0x8000 else raw
                if self.stack[-1]:
                    self.ip += offset

            elif op == Op.CALL:
                argc = self.chunk.bytecode[self.ip]
                self.ip += 1
                args = [self.stack.pop() for _ in range(argc)][::-1]
                callee = self.stack.pop()
                result = self._call_func(callee, args)
                self.stack.append(result)

            elif op == Op.RETURN:
                return self.stack.pop()

            elif op == Op.CLOSURE:
                const_idx = (self.chunk.bytecode[self.ip] << 8) | self.chunk.bytecode[self.ip + 1]
                self.ip += 2
                arity = self.chunk.bytecode[self.ip]
                self.ip += 1
                fn_chunk = self.chunk.constants[const_idx]
                fn = VMFunction(fn_chunk, arity)
                self.stack.append(VMClosure(fn))

            elif op == Op.MAKE_LIST:
                argc = (self.chunk.bytecode[self.ip] << 8) | self.chunk.bytecode[self.ip + 1]
                self.ip += 2
                items = [self.stack.pop() for _ in range(argc)][::-1]
                self.stack.append(items)

            elif op == Op.INDEX:
                index = self.stack.pop()
                obj = self.stack.pop()
                self.stack.append(obj[index])

            elif op == Op.PRINT:
                val = self.stack.pop()
                print(self._to_str(val))
                self.stack.append(None)

            else:
                raise VMError(f"Unknown opcode: {op}")

        return self.stack[-1] if self.stack else None

    def _call_func(self, callee, args):
        if isinstance(callee, tuple) and callee[0] == "builtin":
            fn, arity = callee[1], callee[2]
            if arity >= 0 and len(args) != arity:
                raise VMError(f"Expected {arity} args, got {len(args)}")
            return fn(args)
        if isinstance(callee, VMClosure):
            fn = callee.fn
            if len(args) != fn.arity:
                raise VMError(f"{fn.name} expected {fn.arity} args, got {len(args)}")
            old_chunk = self.chunk
            old_ip = self.ip
            self.chunk = fn.chunk
            self.ip = 0
            # Push args as globals (simplified)
            for i, (pname, _) in enumerate(fn.chunk.names[:fn.arity]):
                if i < len(args):
                    self.globals[pname] = args[i]
            result = self._run()
            self.chunk = old_chunk
            self.ip = old_ip
            return result
        if isinstance(callee, VMFunction):
            if hasattr(callee, '_native'):
                return callee._native(args)
            old_chunk = self.chunk
            old_ip = self.ip
            self.chunk = callee.chunk
            self.ip = 0
            for i, name in enumerate(callee.chunk.names[:callee.arity]):
                if i < len(args):
                    self.globals[name] = args[i]
            result = self._run()
            self.chunk = old_chunk
            self.ip = old_ip
            return result
        raise VMError(f"Cannot call non-function: {type(callee).__name__}")

    def _to_str(self, val):
        if val is None:
            return "()"
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, list):
            return "[" + ", ".join(self._to_str(v) for v in val) + "]"
        if isinstance(val, tuple):
            return "(" + ", ".join(self._to_str(v) for v in val) + ")"
        return str(val)

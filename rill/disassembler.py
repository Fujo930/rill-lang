from .opcodes import Op
from .compiler import Chunk


def disassemble(chunk: Chunk, name: str = "chunk") -> str:
    lines = []
    lines.append(f"=== {name} ===")
    lines.append(f"constants: {chunk.constants}")
    lines.append(f"names: {chunk.names}")
    lines.append("")

    i = 0
    while i < len(chunk.bytecode):
        op = chunk.bytecode[i]
        i += 1

        try:
            op_name = Op(op).name
        except ValueError:
            op_name = f"OP_{op}"

        if op in (Op.LOAD_CONST, Op.CLOSURE):
            idx = (chunk.bytecode[i] << 8) | chunk.bytecode[i + 1]
            i += 2
            lines.append(f"  {i-3:04d}  {op_name:<16} {idx}")
        elif op in (Op.LOAD_GLOBAL, Op.STORE_GLOBAL):
            idx = (chunk.bytecode[i] << 8) | chunk.bytecode[i + 1]
            i += 2
            name = chunk.names[idx] if idx < len(chunk.names) else f"?{idx}"
            lines.append(f"  {i-3:04d}  {op_name:<16} {idx} ({name})")
        elif op in (Op.JUMP, Op.JUMP_IF_FALSE, Op.JUMP_IF_TRUE):
            offset = (chunk.bytecode[i] << 8) | chunk.bytecode[i + 1]
            i += 2
            lines.append(f"  {i-3:04d}  {op_name:<16} -> {i + offset:04d}")
        elif op == Op.CALL:
            argc = chunk.bytecode[i]
            i += 1
            lines.append(f"  {i-2:04d}  {op_name:<16} {argc}")
        elif op in (Op.MAKE_LIST,):
            argc = (chunk.bytecode[i] << 8) | chunk.bytecode[i + 1]
            i += 2
            lines.append(f"  {i-3:04d}  {op_name:<16} {argc}")
        else:
            lines.append(f"  {i-1:04d}  {op_name}")

    return "\n".join(lines)

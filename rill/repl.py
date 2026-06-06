import sys
from .lexer import Lexer, LexError
from .parser import Parser, ParseError
from .interpreter import Interpreter, RillRuntimeError


def run_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    try:
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()
        interp = Interpreter()
        interp.run(program)
    except LexError as e:
        print(f"Lexer Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ParseError as e:
        print(f"Parse Error: {e}", file=sys.stderr)
        sys.exit(1)
    except RillRuntimeError as e:
        print(f"Runtime Error: {e}", file=sys.stderr)
        sys.exit(1)


def repl():
    print("Rill v0.1.0 (type 'exit' or Ctrl+C to quit)")
    interp = Interpreter()
    buffer = []
    brace_depth = 0

    while True:
        try:
            prompt = "... " if brace_depth > 0 else ">>> "
            line = input(prompt)
            if line.strip() in ("exit", "quit"):
                break
            if not line.strip():
                continue

            buffer.append(line)
            brace_depth += line.count("{") - line.count("}")

            if brace_depth > 0:
                continue

            source = "\n".join(buffer)
            buffer = []
            brace_depth = 0

            tokens = Lexer(source).tokenize()
            program = Parser(tokens).parse()
            result = interp.run(program)
            if result is not None:
                print(interp._to_rill_str(result))

        except (LexError, ParseError) as e:
            # Might be incomplete input
            if "{" in str(e) or "Expected" in str(e):
                brace_depth += 1
                continue
            print(f"Error: {e}", file=sys.stderr)
            buffer = []
            brace_depth = 0
        except RillRuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            buffer = []
            brace_depth = 0
        except (EOFError, KeyboardInterrupt):
            print()
            break


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_file(sys.argv[1])
    else:
        repl()

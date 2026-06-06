<p align="center">
  <img src="https://img.shields.io/badge/version-0.3.0-blue?style=for-the-badge" alt="version">
  <img src="https://img.shields.io/badge/python-3.10+-green?style=for-the-badge&logo=python&logoColor=white" alt="python">
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge" alt="license">
  <img src="https://img.shields.io/badge/tests-49%20passing-brightgreen?style=for-the-badge&logo=pytest&logoColor=white" alt="tests">
  <img src="https://img.shields.io/badge/status-active%20dev-orange?style=for-the-badge" alt="status">
</p>

<h1 align="center">
  <br>
  <code>~ rill ~</code>
  <br>
  <sub>a tiny language where data flows like water</sub>
  <br>
</h1>

<p align="center">
  A minimal, expression-oriented programming language with<br>
  pattern matching, pipe operators, and first-class functions.
</p>

<p align="center">
  Designed & built by <b>mimo-v2.5-free</b> (opencode AI agent)
</p>

---

## Why Rill?

Rill is designed around one idea: **data should flow naturally through functions**, like water through a stream. Every construct is an expression, pattern matching is built-in, and the pipe operator lets you chain operations without nested calls.

```
5 |> double |> add_one |> to_string |> print
```

## Features at a Glance

| Feature | Example |
|---|---|
| **Expression-oriented** | `if x > 0 { x } else { -x }` returns a value |
| **Pattern matching** | `match x { 0 -> "zero", _ -> "other" }` |
| **Pipe operator** | `value \|> fn1 \|> fn2 \|> fn3` |
| **Immutable by default** | `let x = 42` (use `mut` to reassign) |
| **First-class functions** | `let f = fn(x) { x * 2 }` |
| **While loops + break** | `while cond { body }` / `break value` |
| **F-strings** | `f"Hello, {name}!"` |
| **For loops** | `for i in range(1, 10) { ... }` |
| **Closures** | `let add = fn(n) { fn(x) { x + n } }` |

## Quick Start

```bash
# Run a file
python -m rill examples/fib.rill

# Start the REPL
python -m rill
```

### Or install from source

```bash
git clone https://github.com/Fujo930/rill-lang.git
cd rill-lang
pip install -e .
```

## Examples

### Hello World
```rill
print("Hello, World!")
```

### Fibonacci (recursive + pattern matching)
```rill
let fib = fn(n) {
    match n {
        0 -> 0,
        1 -> 1,
        _ -> fib(n - 1) + fib(n - 2),
    }
}

print(fib(10))  # 55
```

### Pipeline — data flows through functions
```rill
let double = fn(x) { x * 2 }
let add_one = fn(x) { x + 1 }
let square  = fn(x) { x * x }

let result = 5 |> double |> add_one |> square
print(result)  # 121
```

### Pattern Matching with Destructuring
```rill
let classify = fn(x, y) {
    match (x, y) {
        (0, 0) -> "origin",
        (x, 0) -> "on x-axis",
        (0, y) -> "on y-axis",
        _      -> "somewhere else",
    }
}

print(classify(0, 5))  # "on y-axis"
```

### FizzBuzz
```rill
for i in range(1, 101) {
    match (i % 3, i % 5) {
        (0, 0) -> print("FizzBuzz"),
        (0, _) -> print("Fizz"),
        (_, 0) -> print("Buzz"),
        _      -> print(i),
    }
}
```

### While Loop + Break with Value
```rill
let mut i = 0
let result = while true {
    i = i + 1
    if i * i > 50 { break i }
}
print(f"First square > 50: {result}")  # 8
```

### F-strings
```rill
let name = "Rill"
let version = "0.2.0"
print(f"{name} v{version} — a tiny language")
```

## Language Syntax

<details>
<summary><b>Variables</b></summary>

```rill
let x = 42            # immutable
let mut y = 10        # mutable
y = y + 1             # OK — y is mutable
```
</details>

<details>
<summary><b>Functions</b></summary>

```rill
# Full form
let add = fn(a: Int, b: Int) -> Int { a + b }

# Type inference
let double = fn(x) { x * 2 }

# Closure
let make_adder = fn(n) {
    fn(x) { x + n }
}
let add5 = make_adder(5)
print(add5(10))  # 15
```
</details>

<details>
<summary><b>Control Flow</b></summary>

```rill
# If/else (returns a value)
let sign = if x > 0 { 1 } else if x < 0 { -1 } else { 0 }

# While loops
let mut i = 0
while i < 10 {
    i = i + 1
}

# For loops
for i in range(1, 6) {
    print(i)
}

# Break with value
let mut n = 0
let found = while true {
    n = n + 1
    if n > 100 { break n }
}
```
</details>

<details>
<summary><b>Pattern Matching</b></summary>

```rill
match value {
    0          -> "zero",
    n if n > 0 -> "positive",
    _          -> "negative",
}

# Tuple destructuring
match (x, y) {
    (0, 0) -> "origin",
    _      -> "other",
}
```
</details>

<details>
<summary><b>Pipe Operator</b></summary>

```rill
# Instead of: to_string(add_one(double(5)))
# Write:
5 |> double |> add_one |> to_string

# Chain as many as you want
data |> parse |> validate |> transform |> save
```
</details>

## Project Structure

```
rill-lang/
├── rill/                  # Core language implementation
│   ├── tokens.py          # Token types and keywords
│   ├── lexer.py           # Lexical analysis
│   ├── ast_nodes.py       # AST node definitions
│   ├── parser.py          # Parsing / AST construction
│   ├── interpreter.py     # Tree-walk interpreter
│   ├── repl.py            # REPL and file runner
│   └── __main__.py        # Entry point
├── tests/                 # 42 passing tests
│   └── test_rill.py
├── examples/              # Example programs
│   ├── fib.rill
│   ├── fizzbuzz.rill
│   ├── pipeline.rill
│   └── while_demo.rill
├── SPEC.md                # Language specification
├── ROADMAP.md             # Development plan
└── setup.py               # Package setup
```

## Roadmap

| Version | Status | Highlights |
|---|---|---|
| **v0.1.0** | Done | Lexer, Parser, Interpreter, Pattern matching, Pipes |
| **v0.2.0** | Done | While loops, Break/Continue, F-strings |
| **v0.3.0** | Done | Struct, Enum, Impl blocks, Methods |
| **v0.4.0** | Planned | Standard library (map, filter, fold, IO) |
| **v0.5.0** | Planned | Bytecode compiler + VM |
| **v0.6.0** | Planned | LSP server, Formatter, Linter |
| **v0.7.0** | Planned | FFI (C, Python), JSON, HTTP |
| **v1.0.0** | Future | Bootstrapped compiler, Package registry |

See [ROADMAP.md](ROADMAP.md) for the full development plan.

## Built With

- **Python 3.10+** — implementation language
- **pytest** — testing framework

## Credits

Designed and implemented by **mimo-v2.5-free** (opencode AI agent) — an autonomous coding agent that designed the language spec, wrote the lexer, parser, interpreter, tests, and all examples in a single session.

## License

MIT License. See [LICENSE](LICENSE) for details.

---

<p align="center">
  <i>If you find Rill interesting, give it a star!</i>
</p>

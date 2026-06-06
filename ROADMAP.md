# Rill Development Roadmap

> Designed & built by **mimo-v2.5-free** (opencode AI agent)

## v0.2.0 — Core Language Improvements

- [ ] **While loops** — `while condition { body }`
- [ ] **Break / Continue** — loop control flow
- [ ] **String interpolation** — `f"Hello, {name}!"`
- [ ] **Multi-line strings** — triple-quote strings
- [ ] **Comments** — `# single line` (already lexed, support in parser)
- [ ] **Else-if chains** — `else if` shorthand
- [ ] **Assignment expressions** — `x = 5` returns the value

## v0.3.0 — Type System

- [ ] **Struct types** — `struct Point { x: Int, y: Int }`
- [ ] **Enum types** — `enum Color { Red, Green, Blue }`
- [ ] **Method syntax** — `impl Point { fn distance(self) -> Float { ... } }`
- [ ] **Type checking pass** — static analysis before interpretation
- [ ] **Generic functions** — `fn first<T>(list: List<T>) -> T { ... }`
- [ ] **Option<T> / Result<T, E>** — algebraic data types

## v0.4.0 — Standard Library

- [ ] **String module** — split, join, contains, replace, trim
- [ ] **Math module** — abs, min, max, pow, sqrt
- [ ] **List module** — map, filter, fold, sort, reverse, flatten
- [ ] **IO module** — read_file, write_file, stdin
- [ ] **Iterators** — lazy sequences, yield

## v0.5.0 — Compilation

- [ ] **Bytecode compiler** — replace tree-walk interpreter
- [ ] **Virtual machine** — stack-based VM execution
- [ ] **Optimization passes** — constant folding, dead code elimination
- [ ] **Bytecode disassembler** — debug tool

## v0.6.0 — Tooling

- [ ] **LSP server** — language server for IDE support
- [ ] **Formatter** — `rill fmt` code formatter
- [ ] **Linter** — `rill lint` static analysis
- [ ] **Package manager** — `rill pkg install <name>`
- [ ] **REPL improvements** — multiline editing, history, tab completion

## v0.7.0 — Foreign Function Interface

- [ ] **C FFI** — call C libraries from Rill
- [ ] **Python bridge** — import Python modules in Rill
- [ ] **JSON support** — parse and generate JSON
- [ ] **HTTP client** — built-in HTTP requests

## v1.0.0 — Stable Release

- [ ] **Complete standard library**
- [ ] **Performance benchmarks** vs Python/Ruby/Lua
- [ ] **Comprehensive documentation**
- [ ] **Tutorial and book**
- [ ] **Package registry** — rill-lang.dev
- [ ] **Bootstrapped compiler** — Rill compiles itself

---

## Completed

- [x] v0.1.0 — Initial release
  - Lexer, Parser, Interpreter
  - Pattern matching, pipe operators
  - Functions, closures, for loops
  - 31 passing tests

- [x] v0.2.0 — Core Language Improvements
  - While loops with break/continue
  - Break with return value (`break expr`)
  - F-string interpolation (`f"Hello, {name}!"`)
  - 42 passing tests

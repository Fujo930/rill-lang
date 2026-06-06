# Rill

A minimal, expression-oriented programming language with static typing, pattern matching, and pipe operators.

## Features

- **Everything is an expression** — all constructs return a value
- **Pattern matching** — powerful match expressions with destructuring
- **Pipe operator** — chain functions naturally with `|>`
- **Immutable by default** — `let` bindings are immutable, `let mut` for mutability
- **First-class functions** — closures, higher-order functions
- **Clean syntax** — minimal boilerplate

## Quick Start

### Run a file
```bash
python -m rill.repl examples/fib.rill
```

### Start the REPL
```bash
python -m rill.repl
```

## Examples

### Hello World
```rill
print("Hello, World!")
```

### Fibonacci
```rill
let fib = fn(n: Int) -> Int {
    match n {
        0 -> 0,
        1 -> 1,
        _ -> fib(n - 1) + fib(n - 2),
    }
}

print(fib(10))
```

### Pattern Matching
```rill
let describe = fn(x) {
    match x {
        0 -> "zero",
        1 -> "one",
        2 -> "two",
        _ -> "many",
    }
}

print(describe(0))  # "zero"
print(describe(5))  # "many"
```

### Pipeline
```rill
let double = fn(x) { x * 2 }
let add_one = fn(x) { x + 1 }

let result = 5 |> double |> add_one
print(result)  # 11
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

## Syntax

### Variables
```rill
let x = 42            # immutable
let mut y = 10        # mutable
```

### Functions
```rill
let add = fn(a, b) { a + b }
let greet = fn(name: String) -> String { "Hello, " + name }
```

### Control Flow
```rill
if x > 0 { "positive" } else { "non-positive" }
```

### Pattern Matching
```rill
match value {
    0          -> "zero",
    n if n > 0 -> "positive",
    _          -> "negative",
}
```

### Pipe Operator
```rill
value |> function1 |> function2 |> function3
```

## License

MIT

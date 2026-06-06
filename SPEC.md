# Rill Language Specification

Rill is a minimal, expression-oriented programming language with static typing,
pattern matching, and pipe operators.

## Design Principles

- Everything is an expression (returns a value)
- Static typing with type inference
- Pattern matching as a core feature
- Pipe operator for data flow
- Immutable by default
- Clean, minimal syntax

## Types

```
Int     - 64-bit integers       42, -7, 0
Float   - 64-bit floats         3.14, -1.0
Bool    - boolean               true, false
String  - UTF-8 strings         "hello"
Unit    - empty value            ()
Fn      - functions              fn(x) -> x + 1
```

## Syntax

### Variables
```
let x = 42          # immutable binding
let mut x = 42      # mutable binding
```

### Functions
```
let add = fn(a: Int, b: Int) -> Int { a + b }

# Single expression bodies can omit braces
let double = fn(x: Int) -> Int { x * 2 }

# Type inference for params and return
let identity = fn(x) { x }
```

### Control Flow
```
if condition { value } else { other }
if condition { value }   # else branch returns Unit

match value {
    pattern1 -> result1,
    pattern2 -> result2,
    _        -> default,
}
```

### Pattern Matching
```
match x {
    0          -> "zero",
    1          -> "one",
    n if n > 0 -> "positive",
    _          -> "negative",
}

# Destructuring
match pair {
    (0, 0)    -> "origin",
    (x, 0)    -> "on x-axis",
    (0, y)    -> "on y-axis",
    (x, y)    -> "point",
}
```

### Pipe Operator
```
let result = value |> function
                  |> another_function
                  |> yet_another

# Equivalent to: yet_another(another_function(function(value)))
```

### Operators
```
Arithmetic:  +  -  *  /  %
Comparison:  == !=  <  >  <=  >=
Logical:     && ||
Pipe:        |>
Access:      .
```

## Built-in Functions

```
print(value)         - print to stdout
len(collection)      - length of string/list
range(start, end)    - generate integer range
```

## Example Programs

### FizzBuzz
```
for i in range(1, 101) {
    match (i % 3, i % 5) {
        (0, 0) -> print("FizzBuzz"),
        (0, _) -> print("Fizz"),
        (_, 0) -> print("Buzz"),
        _      -> print(i),
    }
}
```

### Fibonacci
```
let fib = fn(n: Int) -> Int {
    match n {
        0 -> 0,
        1 -> 1,
        _ -> fib(n - 1) + fib(n - 2),
    }
}

print(fib(10))
```

### Pipeline Example
```
let square = fn(x: Int) -> Int { x * x }
let add = fn(a: Int) -> Int -> Int { fn(b) { a + b } }

let result = 5 |> square |> add(3) |> print
```

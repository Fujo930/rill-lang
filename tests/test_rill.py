import pytest
from rill.lexer import Lexer, LexError
from rill.parser import Parser, ParseError
from rill.interpreter import Interpreter, RillRuntimeError
from rill.tokens import TokenType


def run(source: str) -> any:
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    interp = Interpreter()
    return interp.run(program)


class TestLexer:
    def test_numbers(self):
        tokens = Lexer("42 3.14").tokenize()
        assert tokens[0].type == TokenType.INT
        assert tokens[0].value == 42
        assert tokens[1].type == TokenType.FLOAT
        assert tokens[1].value == 3.14

    def test_strings(self):
        tokens = Lexer('"hello"').tokenize()
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "hello"

    def test_keywords(self):
        tokens = Lexer("let mut fn if else match for in return").tokenize()
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert types == [
            TokenType.LET, TokenType.MUT, TokenType.FN,
            TokenType.IF, TokenType.ELSE, TokenType.MATCH,
            TokenType.FOR, TokenType.IN, TokenType.RETURN,
        ]

    def test_operators(self):
        tokens = Lexer("+ - * / % == != < > <= >= && || |> ->").tokenize()
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert types == [
            TokenType.PLUS, TokenType.MINUS, TokenType.STAR,
            TokenType.SLASH, TokenType.PERCENT, TokenType.EQ,
            TokenType.NEQ, TokenType.LT, TokenType.GT,
            TokenType.LTE, TokenType.GTE, TokenType.AND,
            TokenType.OR, TokenType.PIPE, TokenType.ARROW,
        ]

    def test_bools(self):
        tokens = Lexer("true false").tokenize()
        assert tokens[0].value is True
        assert tokens[1].value is False

    def test_unterminated_string(self):
        with pytest.raises(LexError):
            Lexer('"unterminated').tokenize()


class TestParser:
    def test_int_literal(self):
        program = run("42")
        assert program == 42

    def test_arithmetic(self):
        assert run("2 + 3") == 5
        assert run("10 - 4") == 6
        assert run("3 * 7") == 21
        assert run("10 / 3") == 3
        assert run("10 % 3") == 1

    def test_unary(self):
        assert run("-5") == -5
        assert run("!true") is False

    def test_comparison(self):
        assert run("3 == 3") is True
        assert run("3 != 3") is False
        assert run("3 < 5") is True
        assert run("3 > 5") is False
        assert run("3 <= 3") is True
        assert run("3 >= 5") is False

    def test_string_concat(self):
        assert run('"hello" + " " + "world"') == "hello world"

    def test_let_binding(self):
        assert run("let x = 10\nx") == 10

    def test_function(self):
        src = """
let add = fn(a, b) { a + b }
add(2, 3)
"""
        assert run(src) == 5

    def test_higher_order(self):
        src = """
let apply = fn(f, x) { f(x) }
let double = fn(x) { x * 2 }
apply(double, 5)
"""
        assert run(src) == 10

    def test_closure(self):
        src = """
let make_adder = fn(n) {
    fn(x) { x + n }
}
let add5 = make_adder(5)
add5(10)
"""
        assert run(src) == 15

    def test_if_expression(self):
        src = 'if true { 42 } else { 0 }'
        assert run(src) == 42

    def test_if_false(self):
        src = 'if false { 42 } else { 0 }'
        assert run(src) == 0

    def test_match(self):
        src = """
match 2 {
    1 -> "one",
    2 -> "two",
    _ -> "other",
}
"""
        assert run(src) == "two"

    def test_match_wildcard(self):
        src = """
match 99 {
    1 -> "one",
    _ -> "other",
}
"""
        assert run(src) == "other"

    def test_for_loop(self):
        src = """
let mut sum = 0
for i in [1, 2, 3] {
    sum = sum + i
}
sum
"""
        assert run(src) == 6

    def test_pipe(self):
        src = """
let double = fn(x) { x * 2 }
5 |> double
"""
        assert run(src) == 10

    def test_nested_pipe(self):
        src = """
let double = fn(x) { x * 2 }
let add_one = fn(x) { x + 1 }
5 |> double |> add_one
"""
        assert run(src) == 11

    def test_fibonacci(self):
        src = """
let fib = fn(n) {
    match n {
        0 -> 0,
        1 -> 1,
        _ -> fib(n - 1) + fib(n - 2),
    }
}
fib(10)
"""
        assert run(src) == 55

    def test_string_interpolation_concat(self):
        assert run('"Hello, " + "World!"') == "Hello, World!"

    def test_range_and_for(self):
        src = """
let mut sum = 0
for i in range(1, 6) {
    sum = sum + i
}
sum
"""
        assert run(src) == 15

    def test_list_literal(self):
        src = "[1, 2, 3]"
        result = run(src)
        assert result == [1, 2, 3]

    def test_list_index(self):
        src = """
let xs = [10, 20, 30]
xs[1]
"""
        assert run(src) == 20

    def test_division_float(self):
        assert run("6.0 / 4") == 1.5

    def test_bool_ops(self):
        assert run("true && false") is False
        assert run("true || false") is True


class TestIntegration:
    def test_fizzbuzz_first_few(self):
        src = """
let mut results = []
for i in range(1, 16) {
    match (i % 3, i % 5) {
        (0, 0) -> { results = results + ["FizzBuzz"] },
        (0, _) -> { results = results + ["Fizz"] },
        (_, 0) -> { results = results + ["Buzz"] },
        _      -> { results = results + [i] },
    }
}
results
"""
        result = run(src)
        assert result[:5] == [1, 2, "Fizz", 4, "Buzz"]

    def test_string_ops(self):
        assert run('"abc" + "def"') == "abcdef"


class TestV02:
    def test_while_loop(self):
        src = """
let mut i = 0
while i < 5 {
    i = i + 1
}
i
"""
        assert run(src) == 5

    def test_while_false(self):
        assert run("while false { 42 }") is None

    def test_break(self):
        src = """
let mut i = 0
while true {
    if i == 3 { break }
    i = i + 1
}
i
"""
        assert run(src) == 3

    def test_break_with_value(self):
        src = """
let mut i = 0
while true {
    i = i + 1
    if i == 5 { break i * 2 }
}
"""
        assert run(src) == 10

    def test_continue(self):
        src = """
let mut sum = 0
let mut i = 0
while i < 10 {
    i = i + 1
    if i % 2 == 0 { continue }
    sum = sum + i
}
sum
"""
        assert run(src) == 25

    def test_fstring(self):
        src = 'let x = 42\nf"Value: {x}"'
        assert run(src) == "Value: 42"

    def test_fstring_expr(self):
        assert run('f"{2 + 3}"') == "5"

    def test_fstring_nested(self):
        src = """
let name = "Rill"
f"Language: {name}"
"""
        assert run(src) == "Language: Rill"

    def test_break_in_for(self):
        src = """
let mut sum = 0
for i in range(1, 100) {
    if i > 5 { break }
    sum = sum + i
}
sum
"""
        assert run(src) == 15

    def test_continue_in_for(self):
        src = """
let mut sum = 0
for i in range(1, 11) {
    if i % 2 == 0 { continue }
    sum = sum + i
}
sum
"""
        assert run(src) == 25

    def test_while_with_break_and_continue(self):
        src = """
let mut result = []
let mut i = 0
while i < 10 {
    i = i + 1
    if i % 3 == 0 { continue }
    if i == 8 { break }
    result = result + [i]
}
result
"""
        assert run(src) == [1, 2, 4, 5, 7]


class TestV03:
    def test_struct_basic(self):
        src = """
struct Point {
    x: Int,
    y: Int,
}
let p = Point { x: 3, y: 4 }
p.x + p.y
"""
        assert run(src) == 7

    def test_struct_method(self):
        src = """
struct Point {
    x: Int,
    y: Int,
}
impl Point {
    fn distance(self) {
        self.x * self.x + self.y * self.y
    }
}
let p = Point { x: 3, y: 4 }
p.distance()
"""
        assert run(src) == 25

    def test_struct_static_method(self):
        src = """
struct Point {
    x: Int,
    y: Int,
}
impl Point {
    fn new(x, y) {
        Point { x: x, y: y }
    }
}
let p = Point.new(10, 20)
p.x
"""
        assert run(src) == 10

    def test_enum_basic(self):
        src = """
enum Color {
    Red,
    Green,
    Blue,
}
let c = Color.Green
"""
        result = run(src)
        assert result.variant_name == "Green"

    def test_enum_with_data(self):
        src = """
enum Shape {
    Circle(Float),
    Rect(Float, Float),
}
Shape.Circle(3.14)
"""
        result = run(src)
        assert result.variant_name == "Circle"
        assert result.data == (3.14,)

    def test_struct_enum_combo(self):
        src = """
enum Direction {
    North,
    South,
}
struct Player {
    name: String,
    hp: Int,
}
impl Player {
    fn new(name) {
        Player { name: name, hp: 100 }
    }
    fn is_alive(self) {
        self.hp > 0
    }
}
let p = Player.new("Hero")
p.is_alive()
"""
        assert run(src) is True

    def test_struct_print(self):
        src = """
struct Vec2 {
    x: Int,
    y: Int,
}
let v = Vec2 { x: 1, y: 2 }
f"{v}"
"""
        assert run(src) == "Vec2 { x: 1, y: 2 }"


class TestV04:
    def test_map(self):
        assert run('map([1, 2, 3], fn(x) { x * 2 })') == [2, 4, 6]

    def test_filter(self):
        assert run('filter([1, 2, 3, 4, 5], fn(x) { x % 2 == 0 })') == [2, 4]

    def test_fold(self):
        assert run('fold([1, 2, 3, 4, 5], fn(a, x) { a + x }, 0)') == 15

    def test_reduce(self):
        assert run('reduce([1, 2, 3, 4, 5], fn(a, x) { a + x })') == 15

    def test_sort(self):
        assert run('sort([3, 1, 4, 1, 5])') == [1, 1, 3, 4, 5]

    def test_reverse(self):
        assert run('reverse([1, 2, 3])') == [3, 2, 1]

    def test_flatten(self):
        assert run('flatten([[1, 2], [3, 4]])') == [1, 2, 3, 4]

    def test_head_tail(self):
        assert run('head([1, 2, 3])') == 1
        assert run('tail([1, 2, 3])') == [2, 3]

    def test_cons(self):
        assert run('cons(0, [1, 2, 3])') == [0, 1, 2, 3]

    def test_sum(self):
        assert run('sum([1, 2, 3, 4, 5])') == 15

    def test_contains(self):
        assert run('contains([1, 2, 3], 2)') is True
        assert run('contains([1, 2, 3], 99)') is False

    def test_unique(self):
        assert run('unique([1, 2, 2, 3, 3, 3])') == [1, 2, 3]

    def test_take_drop(self):
        assert run('take([1, 2, 3, 4, 5], 3)') == [1, 2, 3]
        assert run('drop([1, 2, 3, 4, 5], 2)') == [3, 4, 5]

    def test_chunks(self):
        assert run('chunks([1, 2, 3, 4, 5], 2)') == [[1, 2], [3, 4], [5]]

    def test_split_join(self):
        assert run('split("a,b,c", ",")') == ["a", "b", "c"]
        assert run('join(["x", "y"], "-")') == "x-y"

    def test_str_ops(self):
        assert run('upper("hello")') == "HELLO"
        assert run('lower("WORLD")') == "world"
        assert run('trim("  hi  ")') == "hi"
        assert run('starts_with("Hello", "He")') is True
        assert run('ends_with("Hello", "lo")') is True
        assert run('replace("foo bar", "bar", "baz")') == "foo baz"

    def test_math(self):
        assert run('abs(-42)') == 42
        assert run('sqrt(16)') == 4.0
        assert run('pow(2, 10)') == 1024
        assert run('floor(3.7)') == 3

    def test_zip_enumerate(self):
        result = run('zip(["a", "b"], [1, 2])')
        assert result == [("a", 1), ("b", 2)]
        result = run('enumerate(["x", "y"])')
        assert result == [(0, "x"), (1, "y")]

    def test_any_all(self):
        assert run('any([0, 0, 1])') is True
        assert run('any([0, 0, 0])') is False
        assert run('all([1, 1, 1])') is True
        assert run('all([1, 0, 1])') is False

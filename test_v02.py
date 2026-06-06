from rill.lexer import Lexer
from rill.parser import Parser
from rill.interpreter import Interpreter

def run(src):
    tokens = Lexer(src).tokenize()
    program = Parser(tokens).parse()
    interp = Interpreter()
    return interp.run(program)

# while loop
print("=== while loop ===")
run('''
let mut i = 0
while i < 5 {
    print(i)
    i = i + 1
}
''')

# break
print("=== break ===")
run('''
let mut i = 0
while true {
    if i == 3 { break }
    print(i)
    i = i + 1
}
''')

# continue
print("=== continue ===")
run('''
for i in range(1, 6) {
    if i % 2 == 0 { continue }
    print(i)
}
''')

# f-string
print("=== f-string ===")
run('''
let name = "World"
let age = 42
print(f"Hello, {name}! Age: {age}")
''')

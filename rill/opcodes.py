from enum import IntEnum, auto


class Op(IntEnum):
    # Constants
    LOAD_CONST = auto()     # Push constant
    LOAD_TRUE = auto()      # Push true
    LOAD_FALSE = auto()     # Push false
    LOAD_NULL = auto()      # Push null

    # Variables
    LOAD_LOCAL = auto()     # Load local variable by index
    STORE_LOCAL = auto()    # Store local variable by index
    LOAD_GLOBAL = auto()    # Load global by name index
    STORE_GLOBAL = auto()   # Store global by name index

    # Stack
    POP = auto()            # Discard top
    DUP = auto()            # Duplicate top

    # Arithmetic
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()
    NEG = auto()            # Unary minus

    # Comparison
    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LTE = auto()
    GTE = auto()

    # Logical
    AND = auto()
    OR = auto()
    NOT = auto()

    # Control flow
    JUMP = auto()           # Unconditional jump (offset u16)
    JUMP_IF_FALSE = auto()  # Pop, jump if false
    JUMP_IF_TRUE = auto()   # Pop, jump if true

    # Functions
    CALL = auto()           # Call with N args
    RETURN = auto()         # Return top of stack
    CLOSURE = auto()        # Create closure from function

    # Iterables
    MAKE_LIST = auto()      # Make list from N items
    MAKE_TUPLE = auto()     # Make tuple from N items
    INDEX = auto()          # Index subscript
    INDEX_ASSIGN = auto()   # Index assignment

    # Loops
    BREAK = auto()          # Break out of loop
    CONTINUE = auto()       # Continue to next iteration

    # Print
    PRINT = auto()          # Print top of stack

    # Struct / Enum
    MAKE_STRUCT = auto()    # Define struct type
    MAKE_INSTANCE = auto()  # Create instance
    GET_FIELD = auto()      # Get field by name
    SET_FIELD = auto()      # Set field by name

    # Halt
    HALT = auto()           # Stop execution

import re

# This is a teaching version of the Irony language that does not have
# FOR loops. The idea is for the student to add them. The "deep" and
# for_loop" programs won't work until the for loop is implemented
# correctly. Before addressing FOR, which is somewhat complex, the
# student should study the implementation of IF, and add various
# version of IF other than IF< which is the only only one implemented
# at the moment. This will give the student a good sense of what's
# required in code generation. Note that extending IF rquires adding
# code to code generation and to execution, whereas if one has already
# implemented the extended IF, adding FOR should only require
# extending the parser and the code generator. (For uses all the same
# machinery as is already there for the extneded IFs. In fact,
# depending on exactly how you implement FOR's code generation, you
# may only need to add one additional IF condition.

sources = [ 

    ["fib",
     ["def fib n",
      "if n < 2",
      "return n",
      "end",
      "a = fib n - 1",
      "b = fib n - 2",
      "return a + b",
      "end",
      "",
      "main = fib 9",
      "print main"]],

    ["exp2",
     ["def exp2 c",
      "if c < 1",
      "return 1",
      "end",
      "d = c - 1",
      "e = exp2 d",
      "return e + e",
      "end",
      "result = exp2 10",
      "print result"]],

    ["square",
     ["def square c",
      "if c < 2",
      "return 1",
      "end",
      "b = c - 1",
      "f = square b",
      "d = c + c",
      "e = d - 1",
      "return f + e",
      "end",
      "result = square 8",
      "print result"]],

    ["even_odd",
     ["def is_even n",
      "if n < 1",
      "return 1",
      "end", 
      "return is_odd n - 1",
      "end",
      "",
      "def is_odd n", 
      "if n < 1",
      "return 0",
      "end",
      "return is_even n - 1", 
      "end",
      "",
      "result = is_even 1",
      "print result",
      "result = is_even 2",
      "print result",
      "result = is_even 3",
      "print result",
      "result = is_even 4",
      "print result",
      "result = is_even 5",
      "print result",
      "result = is_even 6",
      "print result"]],

    ["for_loop",
     ["sum = 0",
      "for i from 1 to 5",
      "sum = sum + i",
      "print i",
      "end",
      "print sum",
      "",
      "for j from 10 to 12", 
      "print j",
      "end"]],

    ["deep",
     ["def deep a",
      "sum = 0",
      "for i from 1 to a",
      "print i",
      "for j from a to 1",
      "print j",
      "if i < j",
      "diff = j - i",
      "print diff",
      "sum = sum + diff",
      "end",
      "end",
      "end",
      "return sum",
      "end",
      "r = deep 10",
      "print r"]]
]

# Global state
function_names = set()
counter = 0

# Hardware state
memory = [0] * 512           # Main memory
registers = [0] * 16         # R0-R15 for temp variables
stack = [0] * 16             # Hardware stack
pc = 0                       # Program counter
sp = 0                       # Stack pointer
scope_stack = [{}]           # Variable scopes
next_mem_addr = 0            # Next memory address
output = []                  # Program output

def temp():
    global counter
    counter += 1
    return f"tmp{counter}"

def parse(lines):
    filtered_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            filtered_lines.append(stripped)
    lines = filtered_lines

    pos = [0] # This obscure thing is a python idiom for call by reference.
    
    '''The parser has multiple nested functions (parse_block,
    parse_statement) that all need to advance through the lines
    array. When parse_statement() processes a line, it needs to
    increment the position so that when control returns to
    parse_block(), it knows to continue from the next line.  In
    languages like C++, you'd pass int& pos (reference) or int* pos
    (pointer). In Python, integers are immutable, so you can't modify
    them in-place across function boundaries. Using a list [0] creates
    a mutable container that acts like a reference - all functions
    share the same list object and can modify its contents.  This is a
    common Python idiom for simulating pass-by-reference when you need
    multiple functions to share and modify the same counter/position
    variable.'''

    def parse_block():
        body = []
        while pos[0] < len(lines):
            line = lines[pos[0]]
            if line == "end":
                pos[0] += 1
                break
            body.append(parse_statement())
        return body
    
    def parse_statement():
        line = lines[pos[0]]
        pos[0] += 1
        
        if m := re.match(r"^def (\w+) (\w+)$", line):
            func_name = m[1]
            function_names.add(func_name)
            return {
                "type": "def", 
                "name": func_name, 
                "arg": m[2], 
                "body": parse_block()
            }
        elif m := re.match(r"^if (.+)$", line):
            return {
                "type": "if", 
                "cond": m[1], 
                "body": parse_block()
            }
        elif m := re.match(r"^return (.+)$", line):
            return {"type": "return", "expr": m[1]}
        elif m := re.match(r"^print (.+)$", line):
            return {"type": "print", "expr": m[1]}
        elif m := re.match(r"^(\w+)\s*=\s*(.+)$", line):
            return {"type": "assign", "var": m[1], "expr": m[2]}
        else:
            raise SyntaxError(f"Unknown line: {line}")
    
    ast = []
    while pos[0] < len(lines):
        ast.append(parse_statement())
    
    return ast

def display_ast_tree(ast, indent=0):
    pad = '  ' * indent
    if isinstance(ast, list):
        for item in ast:
            display_ast_tree(item, indent)
    elif isinstance(ast, dict):
        print(f"{pad}{{")
        for key, value in ast.items():
            print(f"{pad}  {repr(key)}:", end=" ")
            if isinstance(value, (dict, list)):
                print()
                display_ast_tree(value, indent + 2)
            else:
                print(repr(value))
        print(f"{pad}}}")
    else:
        print(f"{pad}{repr(ast)}")

def compile_expr(expr):
    expr = expr.strip()

    # Function call
    words = expr.split()
    if len(words) >= 2 and words[0] in function_names:
        fn_name = words[0]
        arg_expr = " ".join(words[1:])
        arg_tmp, arg_code = compile_expr(arg_expr)
        tmp = temp()
        return tmp, arg_code + [
            ("PUSH", arg_tmp),
            ("CALL", fn_name),
            ("MOV", "_retval", tmp)
        ]

    # Binary operations
    if "+" in expr:
        a, b = expr.split("+", 1)
        a, b = a.strip(), b.strip()
        ta, ca = compile_expr(a)
        tb, cb = compile_expr(b)
        t = temp()
        return t, ca + cb + [("ADD", ta, tb, t)]
    elif "-" in expr:
        a, b = expr.split("-", 1)
        a, b = a.strip(), b.strip()
        ta, ca = compile_expr(a)
        tb, cb = compile_expr(b)
        t = temp()
        return t, ca + cb + [("SUB", ta, tb, t)]

    # Number literal or variable
    return expr, []

def compile_stmt(stmt, output):
    if stmt["type"] == "assign":
        t, code = compile_expr(stmt["expr"])
        output.extend(code)
        output.append(("MOV", t, stmt["var"]))
    elif stmt["type"] == "return":
        t, code = compile_expr(stmt["expr"])
        output.extend(code)
        output.append(("RET", t))
    elif stmt["type"] == "if":
        # Parse the condition properly
        if "<" in stmt["cond"]:
            left, right = stmt["cond"].split("<", 1)
            left, right = left.strip(), right.strip()
            
            # Compile both operands
            left_tmp, left_code = compile_expr(left)
            right_tmp, right_code = compile_expr(right)
            
            label = temp()
            output.extend(left_code)
            output.extend(right_code)
            
            # For "if a < b", jump to end when a >= b
            output.append(("JGE", left_tmp, right_tmp, f"{label}_end"))
            
            # Compile the body
            for s in stmt["body"]:
                compile_stmt(s, output)
            output.append(("LABEL", f"{label}_end"))
        else:
            # Handle other comparison operators if needed
            raise SyntaxError(f"Unsupported condition: {stmt['cond']}")
            
    elif stmt["type"] == "print":
        t, code = compile_expr(stmt["expr"])
        output.extend(code)
        output.append(("PRINT", t))

def compile_fn(fn):
    output = [("LABEL", fn["name"]), ("PARAM", fn["arg"])]
    for stmt in fn["body"]:
        compile_stmt(stmt, output)
    return output

def compile_all(ast):
    code = []
    main_code = []

    for item in ast:
        if item["type"] == "def":
            code.extend(compile_fn(item))
        else:
            compile_stmt(item, main_code)

    code.insert(0, ("JMP", "main"))
    code.append(("LABEL", "main"))
    code.extend(main_code)
    code.append(("HALT",))
    return code

# Hardware functions
def is_temp_var(var_name):
    return var_name.startswith('tmp') and var_name[3:].isdigit()

def get_temp_register(var_name):
    if is_temp_var(var_name):
        temp_num = int(var_name[3:])
        return temp_num % 16
    return None

def get_var_addr(var_name):
    global next_mem_addr
    
    if is_temp_var(var_name):
        return None
        
    # Special case for _retval - always use global scope
    if var_name == "_retval":
        global_scope = scope_stack[0]
        if var_name not in global_scope:
            global_scope[var_name] = next_mem_addr
            next_mem_addr += 1
        return global_scope[var_name]
        
    # Always use current scope - don't look through scope stack
    # Each function call gets its own copy of variables
    current_scope = scope_stack[-1]
    if var_name not in current_scope:
        current_scope[var_name] = next_mem_addr
        next_mem_addr += 1
    return current_scope[var_name]

def eval_arg(arg):
    if isinstance(arg, int):
        return arg
    if str(arg).isdigit() or (str(arg).startswith('-') and str(arg)[1:].isdigit()):
        return int(arg)
    elif is_temp_var(arg):
        reg_num = get_temp_register(arg)
        return registers[reg_num]
    else:
        addr = get_var_addr(arg)
        return memory[addr]

def set_var(var_name, value):
    if is_temp_var(var_name):
        reg_num = get_temp_register(var_name)
        registers[reg_num] = value
    else:
        addr = get_var_addr(var_name)
        memory[addr] = value

def push_stack(value):
    global sp
    stack[sp] = value
    sp += 1

def pop_stack():
    global sp
    sp -= 1
    return stack[sp]

def execute(code):
    global pc, sp, output, scope_stack
    
    # Reset hardware state
    pc = 0
    sp = 0
    output = []
    scope_stack = [{}]
    
    # Build label map
    labels = {}
    for i, instr in enumerate(code):
        if instr[0] == "LABEL":
            labels[instr[1]] = i

    print("=== Executing ===")
    
    while pc < len(code):
        instr = code[pc]
        op = instr[0]
        
        print(f"[PC={pc:02}] [SP={sp:02}] {instr}")
        
        if op == "LABEL":
            pass
            
        elif op == "JMP":
            label = instr[1]
            pc = labels[label]
            continue
            
        elif op == "PARAM":
            val = pop_stack()
            set_var(instr[1], val)
            print(f"  → PARAM {instr[1]} = {val}")
            
        elif op == "MOV":
            val = eval_arg(instr[1])
            set_var(instr[2], val)
            dest_loc = "register" if is_temp_var(instr[2]) else "memory"
            print(f"  → MOV {instr[2]} = {val} ({dest_loc})")
            
        elif op == "ADD":
            a = eval_arg(instr[1])
            b = eval_arg(instr[2])
            result = a + b
            set_var(instr[3], result)
            dest_loc = "register" if is_temp_var(instr[3]) else "memory"
            print(f"  → ADD {a} + {b} = {result} → {instr[3]} ({dest_loc})")
            
        elif op == "SUB":
            a = eval_arg(instr[1])
            b = eval_arg(instr[2])
            result = a - b
            set_var(instr[3], result)
            dest_loc = "register" if is_temp_var(instr[3]) else "memory"
            print(f"  → SUB {a} - {b} = {result} → {instr[3]} ({dest_loc})")
            
        elif op == "RET":
            val = eval_arg(instr[1])
            ret_addr = pop_stack()
            scope_stack.pop()
            set_var("_retval", val)
            print(f"  → RET {val} → return to PC={ret_addr}")
            pc = ret_addr
            continue
            
        elif op == "JGE":
            val = eval_arg(instr[1])
            threshold = eval_arg(instr[2])
            label = instr[3]
            if val >= threshold:
                print(f"  → JGE {val} >= {threshold}, jumping to {label}")
                pc = labels[label]
                continue
            else:
                print(f"  → JGE {val} < {threshold}, not jumping")
                
        elif op == "PUSH":
            val = eval_arg(instr[1])
            push_stack(val)
            print(f"  → PUSH {val}")
            
        elif op == "CALL":
            arg = pop_stack()
            ret_addr = pc + 1
            push_stack(ret_addr)
            push_stack(arg)
            scope_stack.append({})
            label = instr[1]
            print(f"  → CALL {label}, arg={arg}, return addr={ret_addr}")
            pc = labels[label]
            continue
            
        elif op == "PRINT":
            val = eval_arg(instr[1])
            output.append(str(val))
            print(f"  → PRINT {val}")
            
        elif op == "HALT":
            print("  → HALT")
            break
            
        else:
            print(f"!! Unknown instruction: {instr}")
            break
            
        pc += 1
    
    print("\n=== Program Output ===")
    print("\n".join(output))

def test_full(source):
    global function_names, counter, next_mem_addr
    
    # Reset global state
    function_names = set()
    counter = 0
    next_mem_addr = 0
    
    print("=== Parsing ===")
    ast = parse(source)
    
    display_ast_tree(ast, indent=0)

    print("=== Compiling ===")
    code = compile_all(ast)
    
    for i, instr in enumerate(code):
        print(f"{i:02}: {instr}")
    
    execute(code)

if __name__ == "__main__":
    [test_full(source[1]) for source in sources]

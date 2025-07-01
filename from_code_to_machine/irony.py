import re

# Global set to track function names for compilation
function_names = set()

# Global counter for temporary variables
counter = 0

def temp():
    """Generate temporary variable names"""
    global counter
    counter += 1
    return f"tmp{counter}"

def parse(lines):
    """Parse Irony source code into AST"""
    lines = [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]
    ast = []
    stack = [ast]

    for line in lines:
        if m := re.match(r"^def (\w+) (\w+)$", line):
            func = {"type": "def", "name": m[1], "arg": m[2], "body": []}
            function_names.add(m[1])
            stack[-1].append(func)
            stack.append(func["body"])
        elif m := re.match(r"^if (.+)$", line):
            node = {"type": "if", "cond": m[1], "body": []}
            stack[-1].append(node)
            stack.append(node["body"])
        elif m := re.match(r"^for (\w+) from (.+) to (.+)$", line):
            node = {"type": "for", "var": m[1], "from": m[2], "to": m[3], "body": []}
            stack[-1].append(node)
            stack.append(node["body"])
        elif m := re.match(r"^return (.+)$", line):
            stack[-1].append({"type": "return", "expr": m[1]})
        elif m := re.match(r"^print (.+)$", line):
            stack[-1].append({"type": "print", "expr": m[1]})
        elif m := re.match(r"^(\w+)\s*=\s*(.+)$", line):
            stack[-1].append({"type": "assign", "var": m[1], "expr": m[2]})
        elif line == "end":
            stack.pop()
        else:
            raise SyntaxError(f"Unknown line: {line}")
    return ast

def compile_expr(expr):
    """Compile expression to assembly code"""
    expr = expr.strip()

    # Check if this is a function call
    words = expr.split()
    if len(words) >= 2 and words[0] in function_names:
        fn_name = words[0]
        arg_expr = " ".join(words[1:])
        arg_tmp, arg_code = compile_expr(arg_expr)
        tmp = temp()
        return tmp, arg_code + [
            f"PUSH {arg_tmp}",
            f"CALL {fn_name}",
            f"MOV _retval {tmp}"
        ]

    # Handle binary operations
    if "+" in expr:
        a, b = expr.split("+")
        a, b = a.strip(), b.strip()
        ta, ca = compile_expr(a)
        tb, cb = compile_expr(b)
        t = temp()
        return t, ca + cb + [f"ADD {ta} {tb} {t}"]
    elif "-" in expr:
        a, b = expr.split("-")
        a, b = a.strip(), b.strip()
        ta, ca = compile_expr(a)
        tb, cb = compile_expr(b)
        t = temp()
        return t, ca + cb + [f"SUB {ta} {tb} {t}"]

    # Number literal or variable
    return expr, []

def compile_stmt(stmt, output):
    """Compile statement to assembly code"""
    if stmt["type"] == "assign":
        t, code = compile_expr(stmt["expr"])
        output.extend(code)
        output.append(f"MOV {t} {stmt['var']}")
    elif stmt["type"] == "return":
        t, code = compile_expr(stmt["expr"])
        output.extend(code)
        output.append(f"RET {t}")
    elif stmt["type"] == "if":
        cond, _ = stmt["cond"].split("<")
        cond = cond.strip()
        t, code = compile_expr(cond)
        label = temp()
        output.extend(code)
        output.append(f"JGE {t} 2 {label}_end")
        for s in stmt["body"]:
            compile_stmt(s, output)
        output.append(f"LABEL {label}_end")
    elif stmt["type"] == "for":
        # Compile for loop: for var from start to end
        start_tmp, start_code = compile_expr(stmt["from"])
        end_tmp, end_code = compile_expr(stmt["to"])
        
        loop_label = temp()
        end_label = temp()
        
        # Initialize loop variable
        output.extend(start_code)
        output.append(f"MOV {start_tmp} {stmt['var']}")
        
        # Store end value in a temp variable
        output.extend(end_code)
        end_var = temp()
        output.append(f"MOV {end_tmp} {end_var}")
        
        # Loop start label
        output.append(f"LABEL {loop_label}_start")
        
        # Check if loop variable > end value, if so jump to end
        output.append(f"JGT {stmt['var']} {end_var} {end_label}_end")
        
        # Loop body
        for s in stmt["body"]:
            compile_stmt(s, output)
        
        # Increment loop variable
        inc_tmp = temp()
        output.append(f"ADD {stmt['var']} 1 {inc_tmp}")
        output.append(f"MOV {inc_tmp} {stmt['var']}")
        
        # Jump back to loop start
        output.append(f"JMP {loop_label}_start")
        
        # End label
        output.append(f"LABEL {end_label}_end")
    elif stmt["type"] == "print":
        t, code = compile_expr(stmt["expr"])
        output.extend(code)
        output.append(f"PRINT {t}")

def compile_fn(fn):
    """Compile function definition to assembly code"""
    output = [f"LABEL {fn['name']}"]
    output.append(f"PARAM {fn['arg']}")
    for stmt in fn["body"]:
        compile_stmt(stmt, output)
    return output

def compile_all(ast):
    """Compile entire AST to assembly code"""
    code = []
    main_code = []

    # Emit functions first
    for item in ast:
        if item["type"] == "def":
            code.extend(compile_fn(item))
        else:
            if item["type"] == "assign":
                compile_stmt(item, main_code)
            elif item["type"] == "print":
                compile_stmt(item, main_code)
            elif item["type"] == "for":
                compile_stmt(item, main_code)

    # Start program with jump to main code
    code.insert(0, "JMP main")
    code.append("LABEL main")
    code.extend(main_code)
    code.append("HALT")
    return code

class VirtualHardware:
    """Virtual machine for executing assembly code"""
    def __init__(self, memory_size=512, stack_size=16):
        # Hardware components
        self.memory = [0] * memory_size      # Main memory
        self.registers = [0] * 16            # General purpose registers R0-R15
        self.stack = [0] * stack_size        # Hardware stack
        
        # Special registers
        self.pc = 0          # Program counter
        self.sp = 0          # Stack pointer
        self.bp = 0          # Base pointer
        
        # Symbol tables for variables and labels
        self.labels = {}         # Maps labels to PC addresses
        self.next_mem_addr = 0   # Next available memory address
        
        # Scoping stack for function calls
        self.scope_stack = [{}]  # Stack of variable scopes
        
        # Program storage
        self.program = []
        self.output = []
        
    def load_program(self, code):
        """Load assembly program and build label map"""
        self.program = code
        self.labels = {}
        
        # First pass: build label map
        for i, line in enumerate(code):
            if line.startswith("LABEL "):
                label_name = line.split()[1]
                self.labels[label_name] = i
    
    def is_temp_var(self, var_name):
        """Check if variable is a temporary (tmp1, tmp2, etc.)"""
        return var_name.startswith('tmp') and var_name[3:].isdigit()
    
    def get_temp_register(self, var_name):
        """Get register number for temp variable (tmp1 -> R1, tmp2 -> R2, etc.)"""
        if self.is_temp_var(var_name):
            temp_num = int(var_name[3:])
            return temp_num % 16  # Wrap around if we have more than 16 temps
        return None
    
    def get_var_addr(self, var_name):
        """Get memory address for variable in current scope, allocate if new"""
        # Temp variables don't get memory addresses - they use registers
        if self.is_temp_var(var_name):
            return None
            
        # Look in current scope first
        current_scope = self.scope_stack[-1]
        if var_name in current_scope:
            return current_scope[var_name]
        
        # Allocate new address for this scope
        addr = self.next_mem_addr
        self.next_mem_addr += 1
        current_scope[var_name] = addr
        return addr
    
    def eval_arg(self, arg):
        """Evaluate argument - could be literal number, register, or memory variable"""
        if arg.isdigit() or (arg.startswith('-') and arg[1:].isdigit()):
            return int(arg)
        elif self.is_temp_var(arg):
            # It's a temp variable - get from register
            reg_num = self.get_temp_register(arg)
            return self.registers[reg_num]
        else:
            # It's a regular variable - get from memory
            addr = self.get_var_addr(arg)
            return self.memory[addr]
    
    def set_var(self, var_name, value):
        """Set variable value in register or memory"""
        if self.is_temp_var(var_name):
            # It's a temp variable - store in register
            reg_num = self.get_temp_register(var_name)
            self.registers[reg_num] = value
        else:
            # It's a regular variable - store in memory
            addr = self.get_var_addr(var_name)
            self.memory[addr] = value
    
    def push(self, value):
        """Push value onto hardware stack"""
        if self.sp >= len(self.stack):
            raise RuntimeError(f"Stack overflow! SP={self.sp}, stack_size={len(self.stack)}")
        self.stack[self.sp] = value
        self.sp += 1
    
    def pop(self):
        """Pop value from hardware stack"""
        if self.sp <= 0:
            raise RuntimeError(f"Stack underflow! SP={self.sp}")
        self.sp -= 1
        return self.stack[self.sp]
    
    def run(self, debug=False):
        """Execute the loaded program"""
        self.pc = 0
        self.sp = 0
        self.output = []
        
        if debug:
            print(f"=== Starting execution with SP={self.sp} ===")
        
        while self.pc < len(self.program):
            instr = self.program[self.pc]
            parts = instr.split()
            op = parts[0]
            
            if debug:
                print(f"[PC={self.pc:02}] [SP={self.sp:02}] {instr}")

            if op == "LABEL":
                pass  # No-op in execution
                
            elif op == "JMP":
                label = parts[1]
                if debug:
                    print(f"  → JMP to {label}")
                self.pc = self.labels[label]
                continue
                
            elif op == "PARAM":
                # Pop argument from stack and store in variable
                val = self.pop()
                self.set_var(parts[1], val)
                if debug:
                    print(f"  → PARAM {parts[1]} = {val}")
                
            elif op == "MOV":
                # MOV src dst
                val = self.eval_arg(parts[1])
                self.set_var(parts[2], val)
                if debug:
                    dest_loc = "register" if self.is_temp_var(parts[2]) else "memory"
                    print(f"  → MOV {parts[2]} = {val} ({dest_loc})")
                
            elif op == "ADD":
                # ADD a b dst
                a = self.eval_arg(parts[1])
                b = self.eval_arg(parts[2])
                result = a + b
                self.set_var(parts[3], result)
                if debug:
                    dest_loc = "register" if self.is_temp_var(parts[3]) else "memory"
                    print(f"  → ADD {a} + {b} = {result} → {parts[3]} ({dest_loc})")
                
            elif op == "SUB":
                # SUB a b dst
                a = self.eval_arg(parts[1])
                b = self.eval_arg(parts[2])
                result = a - b
                self.set_var(parts[3], result)
                if debug:
                    dest_loc = "register" if self.is_temp_var(parts[3]) else "memory"
                    print(f"  → SUB {a} - {b} = {result} → {parts[3]} ({dest_loc})")
                
            elif op == "RET":
                # Return value and jump back
                val = self.eval_arg(parts[1])
                ret_addr = self.pop()
                self.scope_stack.pop()  # Pop current function's scope
                self.set_var("_retval", val)
                if debug:
                    print(f"  → RET {val} → return to PC={ret_addr}")
                self.pc = ret_addr
                continue
                
            elif op == "JGE":
                # JGE val threshold label
                val = self.eval_arg(parts[1])
                threshold = int(parts[2])
                label = parts[3]
                if val >= threshold:
                    if debug:
                        print(f"  → JGE {val} >= {threshold}, jumping to {label}")
                    self.pc = self.labels[label]
                    continue
                else:
                    if debug:
                        print(f"  → JGE {val} < {threshold}, not jumping")
                    
            elif op == "JGT":
                # JGT val threshold label
                val = self.eval_arg(parts[1])
                threshold = self.eval_arg(parts[2])
                label = parts[3]
                if val > threshold:
                    if debug:
                        print(f"  → JGT {val} > {threshold}, jumping to {label}")
                    self.pc = self.labels[label]
                    continue
                else:
                    if debug:
                        print(f"  → JGT {val} <= {threshold}, not jumping")

            elif op == "PUSH":
                # Push value onto stack
                val = self.eval_arg(parts[1])
                self.push(val)
                if debug:
                    print(f"  → PUSH {val}")
                
            elif op == "CALL":
                # Call function - follow original calling convention
                arg = self.pop()       # Pop the argument that was pushed
                ret_addr = self.pc + 1
                self.push(ret_addr)    # Push return address
                self.push(arg)         # Push argument back for PARAM to consume
                self.scope_stack.append({})  # Push new scope for function call
                label = parts[1]
                if debug:
                    print(f"  → CALL {label}, arg={arg}, return addr = {ret_addr}")
                self.pc = self.labels[label]
                continue
                
            elif op == "PRINT":
                # Print value
                val = self.eval_arg(parts[1])
                self.output.append(str(val))
                if debug:
                    print(f"  → PRINT {val}")
                
            elif op == "HALT":
                if debug:
                    print("  → HALT")
                break
                
            else:
                if debug:
                    print(f"!! Unknown instruction: {instr}")
                break
                
            self.pc += 1
        
        return self.output

def compile(source):
    """
    Compile Irony source code to assembly.
    
    Args:
        source: List of strings representing Irony source code lines
        
    Returns:
        List of strings representing assembly instructions
    """
    global function_names, counter
    
    # Reset global state
    function_names = set()
    counter = 0
    
    # Parse and compile
    ast = parse(source)
    assembly = compile_all(ast)
    return assembly

def execute(code, debug=False):
    """
    Execute assembly code on the virtual machine.
    
    Args:
        code: List of strings representing assembly instructions
        debug: If True, print execution trace
        
    Returns:
        List of strings representing program output
    """
    vm = VirtualHardware()
    vm.load_program(code)
    return vm.run(debug=debug)

# Example usage and test cases
if __name__ == "__main__":
    
    # Test case 1: Fibonacci
    fib_source = [
        "def fib n",
        "if n < 2",
        "return n",
        "end",
        "a = fib n - 1",
        "b = fib n - 2",
        "return a + b",
        "end",
        "",
        "main = fib 9",
        "print main",
    ]
    
    # Test case 2: For loops
    for_loop_source = [
        "sum = 0",
        "for i from 1 to 5",
        "sum = sum + i",
        "print i",
        "end",
        "print sum",
        "",
        "for j from 10 to 12", 
        "print j",
        "end"
    ]
    
    # Test case 3: Even/odd mutual recursion
    even_odd_source = [
        "def is_even n",
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
        "result = is_even 6",
        "print result",
        "result = is_even 5",
        "print result",
    ]

    print("=== Testing Fibonacci ===")
    fib_assembly = compile(fib_source)
    fib_output = execute(fib_assembly)
    print("Output:", fib_output)
    
    print("\n=== Testing For Loops ===")
    for_assembly = compile(for_loop_source)
    for_output = execute(for_assembly)
    print("Output:", for_output)
    
    print("\n=== Testing Even/Odd ===")
    even_assembly = compile(even_odd_source)
    even_output = execute(even_assembly)
    print("Output:", even_output)
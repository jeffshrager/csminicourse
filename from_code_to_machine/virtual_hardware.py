class VirtualHardware:
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
        """Load bytecode program and build label map"""
        self.program = code
        self.labels = {}
        
        # First pass: build label map
        for i, line in enumerate(code):
            if line.startswith("LABEL "):
                label_name = line.split()[1]
                self.labels[label_name] = i
                
        print("=== Label Map ===")
        for name, addr in self.labels.items():
            print(f"  {name} => PC {addr}")
        print("=================")
    
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
    
    def run(self):
        """Execute the loaded program"""
        self.pc = 0
        self.sp = 0
        self.output = []
        
        print(f"=== Starting execution with SP={self.sp} ===")
        
        while self.pc < len(self.program):
            instr = self.program[self.pc]
            parts = instr.split()
            op = parts[0]
            
            print(f"[PC={self.pc:02}] [SP={self.sp:02}] {instr}")
            
            #print(self.registers)
            #print(self.stack)
            #print(self.memory)

            if op == "LABEL":
                pass  # No-op in execution
                
            elif op == "JMP":
                label = parts[1]
                print(f"  → JMP to {label}")
                self.pc = self.labels[label]
                continue
                
            elif op == "PARAM":
                # Pop argument from stack and store in variable
                val = self.pop()
                self.set_var(parts[1], val)
                print(f"  → PARAM {parts[1]} = {val}")
                
            elif op == "MOV":
                # MOV src dst
                val = self.eval_arg(parts[1])
                self.set_var(parts[2], val)
                dest_loc = "register" if self.is_temp_var(parts[2]) else "memory"
                print(f"  → MOV {parts[2]} = {val} ({dest_loc})")
                
            elif op == "ADD":
                # ADD a b dst
                a = self.eval_arg(parts[1])
                b = self.eval_arg(parts[2])
                result = a + b
                self.set_var(parts[3], result)
                dest_loc = "register" if self.is_temp_var(parts[3]) else "memory"
                print(f"  → ADD {a} + {b} = {result} → {parts[3]} ({dest_loc})")
                
            elif op == "SUB":
                # SUB a b dst
                a = self.eval_arg(parts[1])
                b = self.eval_arg(parts[2])
                result = a - b
                self.set_var(parts[3], result)
                dest_loc = "register" if self.is_temp_var(parts[3]) else "memory"
                print(f"  → SUB {a} - {b} = {result} → {parts[3]} ({dest_loc})")
                
            elif op == "RET":
                # Return value and jump back
                val = self.eval_arg(parts[1])
                ret_addr = self.pop()
                self.scope_stack.pop()  # Pop current function's scope
                self.set_var("_retval", val)
                print(f"  → RET {val} → return to PC={ret_addr}")
                self.pc = ret_addr
                continue
                
            elif op == "JGE":
                # JGE val threshold label
                val = self.eval_arg(parts[1])
                threshold = int(parts[2])
                label = parts[3]
                if val >= threshold:
                    print(f"  → JGE {val} >= {threshold}, jumping to {label}")
                    self.pc = self.labels[label]
                    continue
                else:
                    print(f"  → JGE {val} < {threshold}, not jumping")
                    
            elif op == "PUSH":
                # Push value onto stack
                val = self.eval_arg(parts[1])
                self.push(val)
                print(f"  → PUSH {val}")
                
            elif op == "CALL":
                # Call function - follow original calling convention
                arg = self.pop()       # Pop the argument that was pushed
                ret_addr = self.pc + 1
                self.push(ret_addr)    # Push return address
                self.push(arg)         # Push argument back for PARAM to consume
                self.scope_stack.append({})  # Push new scope for function call
                label = parts[1]
                print(f"  → CALL {label}, arg={arg}, return addr = {ret_addr}")
                self.pc = self.labels[label]
                continue
                
            elif op == "PRINT":
                # Print value
                val = self.eval_arg(parts[1])
                self.output.append(str(val))
                print(f"  → PRINT {val}")
                
            elif op == "HALT":
                print("  → HALT")
                break
                
            else:
                print(f"!! Unknown instruction: {instr}")
                break
                
            self.pc += 1
        
        print("\n=== Program Output ===")
        print("\n".join(self.output))
        
        print(f"\n=== Final Hardware State ===")
        print(f"PC: {self.pc}")
        print(f"SP: {self.sp}")
        print(f"Active scopes: {len(self.scope_stack)}")
        print(f"Memory variables in current scope:")
        current_scope = self.scope_stack[-1]
        for var, addr in current_scope.items():
            print(f"  {var} @ addr {addr} = {self.memory[addr]}")
        print(f"Registers in use:")
        for i, val in enumerate(self.registers):
            if val != 0:  # Only show non-zero registers
                print(f"  R{i} = {val}")


# Test with the fibonacci bytecode
def test_vh(code):
    vm = VirtualHardware()
    vm.load_program(code)
    vm.run()

fib_code = [
    'JMP main',
    'LABEL fib',
    'PARAM n',
    'JGE n 2 tmp1_end',
    'RET n',
    'LABEL tmp1_end',
    'SUB n 1 tmp2',
    'PUSH tmp2',
    'CALL fib',
    'MOV _retval tmp3',
    'MOV tmp3 a',
    'SUB n 2 tmp4',
    'PUSH tmp4',
    'CALL fib',
    'MOV _retval tmp5',
    'MOV tmp5 b',
    'ADD a b tmp6',
    'RET tmp6',
    'LABEL main',
    'PUSH 9',
    'CALL fib',
    'MOV _retval tmp7',
    'MOV tmp7 main',
    'PRINT main',
    'HALT'
]

even_odd_code = [
    'JMP main',
    'LABEL is_even',
    'PARAM n',
    'JGE n 2 tmp1_end',
    'RET 1',
    'LABEL tmp1_end',
    'SUB n 1 tmp2',
    'PUSH tmp2',
    'CALL is_odd',
    'MOV _retval tmp3',
    'RET tmp3',
    'LABEL is_odd',
    'PARAM n',
    'JGE n 2 tmp4_end',
    'RET 0',
    'LABEL tmp4_end',
    'SUB n 1 tmp5',
    'PUSH tmp5',
    'CALL is_even',
    'MOV _retval tmp6',
    'RET tmp6',
    'LABEL main',
    'PUSH 6',
    'CALL is_even',
    'MOV _retval tmp7',
    'MOV tmp7 result',
    'PRINT result',
    'PUSH 5',
    'CALL is_even',
    'MOV _retval tmp8',
    'MOV tmp8 result',
    'PRINT result',
    'HALT'
]

#test_vh(fib_code)
test_vh(even_odd_code)

#!/usr/bin/env python3
"""
Smiley Programming Language Interpreter
A Turing-complete lambda calculus implementation using ASCII emoticons
"""

import re
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

# ============================================================================
# Abstract Syntax Tree Classes
# ============================================================================

class Expression(ABC):
    """Base class for all expressions in Smiley"""
    @abstractmethod
    def __str__(self) -> str:
        pass

@dataclass
class Variable(Expression):
    """Variable reference"""
    name: str
    
    def __str__(self) -> str:
        return self.name

@dataclass
class Lambda(Expression):
    """Lambda abstraction: λx.e"""
    param: str
    body: Expression
    
    def __str__(self) -> str:
        return f"(λ{self.param}.{self.body})"

@dataclass
class Application(Expression):
    """Function application: f x"""
    func: Expression
    arg: Expression
    
    def __str__(self) -> str:
        return f"({self.func} {self.arg})"

@dataclass
class Primitive(Expression):
    """Built-in primitive values"""
    value: Any
    name: str
    
    def __str__(self) -> str:
        return self.name

@dataclass
class Binding(Expression):
    """Variable binding: let x = e1 in e2"""
    var: str
    value: Expression
    body: Expression
    
    def __str__(self) -> str:
        return f"(let {self.var} = {self.value} in {self.body})"

# ============================================================================
# Tokenizer
# ============================================================================

class SmileyTokenizer:
    """Tokenizes Smiley source code into emoticon tokens"""
    
    EMOTICONS = {
        # Lambda calculus core
        ':)': 'LAMBDA',
        ':(': 'APPLY', 
        ':D': 'BIND',
        ':|': 'IDENTITY',
        ':P': 'TERMINATOR',
        
        # Variables
        ':o': 'VAR_X',
        ':O': 'VAR_Y',
        ':/': 'VAR_Z',
        ':\\': 'VAR_W',
        
        # Booleans
        '^_^': 'TRUE',
        'T_T': 'FALSE',
        '>:(': 'NOT',
        '=D': 'AND',
        'XD': 'OR',
        
        # Numbers (Church numerals)
        '0_0': 'ZERO',
        '1_1': 'ONE',
        '2_2': 'TWO',
        '3_3': 'THREE',
        '4_4': 'FOUR',
        '5_5': 'FIVE',
        
        # Arithmetic
        '+_+': 'SUCC',
        '-_-': 'PRED',
        '*_*': 'MULT',
        '/_/': 'ADD',
        
        # Comparison
        '=_=': 'ISZERO',
        '<_<': 'LT',
        '>_>': 'GT',
        
        # Control flow
        '(^o^)': 'IF',
        '@_@': 'RECURSION',
        'o_O': 'COND',
        
        # Data structures
        '[:]': 'CONS',
        '[:': 'CAR',
        ':]': 'CDR',
        '[]': 'NIL',
        
        # I/O
        '8)': 'PRINT',
        '8(': 'INPUT',
        '8|': 'NEWLINE',
        
        # Punctuation
        '->': 'ARROW',
        '=': 'EQUALS',
    }
    
    def __init__(self, source: str):
        self.source = source
        self.tokens = []
        self.pos = 0
    
    def tokenize(self) -> List[tuple]:
        """Tokenize the source code into (token_type, value) pairs"""
        self.tokens = []
        self.pos = 0
        
        while self.pos < len(self.source):
            # Skip whitespace
            if self.source[self.pos].isspace():
                self.pos += 1
                continue
                
            # Try to match emoticons (longest first)
            matched = False
            for emoticon in sorted(self.EMOTICONS.keys(), key=len, reverse=True):
                if self.source[self.pos:].startswith(emoticon):
                    self.tokens.append((self.EMOTICONS[emoticon], emoticon))
                    self.pos += len(emoticon)
                    matched = True
                    break
            
            if not matched:
                # Handle single characters
                char = self.source[self.pos]
                if char in '()[]{}':
                    self.tokens.append(('PAREN', char))
                elif char.isalnum() or char == '_':
                    # Collect identifier
                    start = self.pos
                    while (self.pos < len(self.source) and 
                           (self.source[self.pos].isalnum() or self.source[self.pos] == '_')):
                        self.pos += 1
                    self.tokens.append(('IDENTIFIER', self.source[start:self.pos]))
                    continue
                else:
                    self.tokens.append(('CHAR', char))
                
                self.pos += 1
        
        return self.tokens

# ============================================================================
# Parser
# ============================================================================

class SmileyParser:
    """Parses Smiley tokens into an Abstract Syntax Tree"""
    
    def __init__(self, tokens: List[tuple]):
        self.tokens = tokens
        self.pos = 0
    
    def current_token(self) -> Optional[tuple]:
        """Get current token"""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None
    
    def consume(self, expected: str = None) -> tuple:
        """Consume current token, optionally checking type"""
        if self.pos >= len(self.tokens):
            raise SyntaxError("Unexpected end of input")
        
        token = self.tokens[self.pos]
        if expected and token[0] != expected:
            raise SyntaxError(f"Expected {expected}, got {token[0]}")
        
        self.pos += 1
        return token
    
    def parse(self) -> Expression:
        """Parse tokens into an expression"""
        return self.parse_expression()
    
    def parse_expression(self) -> Expression:
        """Parse a complete expression"""
        return self.parse_binding()
    
    def parse_binding(self) -> Expression:
        """Parse binding expressions (:D var = expr)"""
        if self.current_token() and self.current_token()[0] == 'BIND':
            self.consume('BIND')
            var_token = self.consume()
            var_name = self.token_to_var_name(var_token)
            self.consume('EQUALS')
            value = self.parse_lambda()
            
            # Look for body after terminator
            if self.current_token() and self.current_token()[0] == 'TERMINATOR':
                self.consume('TERMINATOR')
                if self.pos < len(self.tokens):
                    body = self.parse_expression()
                    return Binding(var_name, value, body)
                else:
                    # If no body, return the value bound to a dummy expression
                    return Binding(var_name, value, Variable(var_name))
            
            return Binding(var_name, value, Variable(var_name))
        
        return self.parse_lambda()
    
    def parse_lambda(self) -> Expression:
        """Parse lambda expressions (:) var -> expr)"""
        if self.current_token() and self.current_token()[0] == 'LAMBDA':
            self.consume('LAMBDA')
            var_token = self.consume()
            var_name = self.token_to_var_name(var_token)
            self.consume('ARROW')
            body = self.parse_application()
            return Lambda(var_name, body)
        
        return self.parse_application()
    
    def parse_application(self) -> Expression:
        """Parse function applications (left-associative)"""
        # Handle explicit application with :(
        if self.current_token() and self.current_token()[0] == 'APPLY':
            self.consume('APPLY')
            func = self.parse_atom()
            arg = self.parse_atom()
            expr = Application(func, arg)
            
            # Continue parsing more applications
            while (self.current_token() and 
                   self.current_token()[0] in ['APPLY', 'VAR_X', 'VAR_Y', 'VAR_Z', 'VAR_W',
                                              'ZERO', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE',
                                              'TRUE', 'FALSE', 'LAMBDA', 'PAREN']):
                if self.current_token()[0] == 'APPLY':
                    self.consume('APPLY')
                    arg = self.parse_atom()
                    expr = Application(expr, arg)
                else:
                    # Implicit application
                    arg = self.parse_atom()
                    expr = Application(expr, arg)
            
            return expr
        else:
            # Normal parsing without explicit application
            expr = self.parse_atom()
            
            while (self.current_token() and 
                   self.current_token()[0] in ['VAR_X', 'VAR_Y', 'VAR_Z', 'VAR_W',
                                              'ZERO', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE',
                                              'TRUE', 'FALSE', 'LAMBDA', 'PAREN']):
                # Implicit application
                arg = self.parse_atom()
                expr = Application(expr, arg)
            
            return expr
    
    def parse_atom(self) -> Expression:
        """Parse atomic expressions"""
        token = self.current_token()
        if not token:
            raise SyntaxError("Unexpected end of input")
        
        token_type, value = token
        
        # Handle explicit application at atom level
        if token_type == 'APPLY':
            return self.parse_application()
        
        # Variables
        if token_type in ['VAR_X', 'VAR_Y', 'VAR_Z', 'VAR_W']:
            self.consume()
            return Variable(self.token_to_var_name(token))
        
        # Primitives
        if token_type in ['TRUE', 'FALSE', 'ZERO', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE']:
            self.consume()
            return self.create_primitive(token_type, value)
        
        # Control flow and recursion
        if token_type in ['SUCC', 'PRED', 'MULT', 'ADD', 'ISZERO', 'NOT', 'AND', 'OR', 'RECURSION', 'PRINT']:
            self.consume()
            return self.create_primitive(token_type, value)
        
        # Conditional expressions
        if token_type == 'IF':
            self.consume()
            return self.create_primitive(token_type, value)
        
        # Identifiers
        if token_type == 'IDENTIFIER':
            self.consume()
            return Variable(value)
        
        # Parenthesized expressions
        if token_type == 'PAREN' and value == '(':
            self.consume()
            expr = self.parse_expression()
            if self.current_token() and self.current_token()[0] == 'PAREN':
                self.consume()
            return expr
        
        # Lambda expressions
        if token_type == 'LAMBDA':
            return self.parse_lambda()
        
        # Skip terminators
        if token_type == 'TERMINATOR':
            self.consume()
            if self.pos < len(self.tokens):
                return self.parse_atom()
            else:
                # Return identity if nothing follows
                return Lambda('x', Variable('x'))
        
        raise SyntaxError(f"Unexpected token: {token}")
    
    def token_to_var_name(self, token: tuple) -> str:
        """Convert variable tokens to variable names"""
        mapping = {
            'VAR_X': 'x',
            'VAR_Y': 'y', 
            'VAR_Z': 'z',
            'VAR_W': 'w'
        }
        return mapping.get(token[0], token[1])
    
    def create_primitive(self, token_type: str, value: str) -> Primitive:
        """Create primitive expressions"""
        # Map Church numerals to their values
        if token_type in ['ZERO', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE']:
            num_map = {'ZERO': 0, 'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5}
            return create_church_numeral(num_map[token_type])
        elif token_type == 'TRUE':
            return create_church_boolean(True)
        elif token_type == 'FALSE':
            return create_church_boolean(False)
        else:
            return Primitive(token_type, value)

# ============================================================================
# Evaluator
# ============================================================================

class SmileyEvaluator:
    """Evaluates Smiley expressions using lambda calculus semantics"""
    
    def __init__(self):
        self.var_counter = 0
        self.environment = {}
    
    def fresh_var(self) -> str:
        """Generate a fresh variable name"""
        self.var_counter += 1
        return f"_v{self.var_counter}"
    
    def substitute(self, expr: Expression, var: str, replacement: Expression) -> Expression:
        """Substitute variable with replacement in expression"""
        if isinstance(expr, Variable):
            return replacement if expr.name == var else expr
        
        elif isinstance(expr, Lambda):
            if expr.param == var:
                return expr  # Variable is bound, no substitution
            else:
                # Alpha conversion if needed
                if self.occurs_free(replacement, expr.param):
                    fresh = self.fresh_var()
                    renamed_body = self.substitute(expr.body, expr.param, Variable(fresh))
                    return Lambda(fresh, self.substitute(renamed_body, var, replacement))
                else:
                    return Lambda(expr.param, self.substitute(expr.body, var, replacement))
        
        elif isinstance(expr, Application):
            return Application(
                self.substitute(expr.func, var, replacement),
                self.substitute(expr.arg, var, replacement)
            )
        
        elif isinstance(expr, Binding):
            if expr.var == var:
                return Binding(expr.var, self.substitute(expr.value, var, replacement), expr.body)
            else:
                return Binding(
                    expr.var,
                    self.substitute(expr.value, var, replacement),
                    self.substitute(expr.body, var, replacement)
                )
        
        else:
            return expr
    
    def occurs_free(self, expr: Expression, var: str) -> bool:
        """Check if variable occurs free in expression"""
        if isinstance(expr, Variable):
            return expr.name == var
        elif isinstance(expr, Lambda):
            return expr.param != var and self.occurs_free(expr.body, var)
        elif isinstance(expr, Application):
            return self.occurs_free(expr.func, var) or self.occurs_free(expr.arg, var)
        elif isinstance(expr, Binding):
            return (self.occurs_free(expr.value, var) or 
                   (expr.var != var and self.occurs_free(expr.body, var)))
        else:
            return False
    
    def evaluate(self, expr: Expression, depth: int = 0) -> Expression:
        """Evaluate expression using beta reduction"""
        if depth > 1000:  # Prevent infinite recursion
            return expr
        
        if isinstance(expr, Variable):
            # Look up in environment
            if expr.name in self.environment:
                return self.environment[expr.name]
            return expr
        
        elif isinstance(expr, Lambda):
            return expr  # Lambdas are values
        
        elif isinstance(expr, Application):
            func = self.evaluate(expr.func, depth + 1)
            
            if isinstance(func, Lambda):
                # Beta reduction
                arg = self.evaluate(expr.arg, depth + 1)
                result = self.substitute(func.body, func.param, arg)
                return self.evaluate(result, depth + 1)
            
            elif isinstance(func, Primitive):
                # Handle built-in operations
                return self.apply_primitive(func, expr.arg, depth)
            
            else:
                # Can't reduce further
                return Application(func, self.evaluate(expr.arg, depth + 1))
        
        elif isinstance(expr, Binding):
            # Evaluate value and bind to variable
            value = self.evaluate(expr.value, depth + 1)
            old_env = self.environment.copy()
            self.environment[expr.var] = value
            result = self.evaluate(expr.body, depth + 1)
            self.environment = old_env
            return result
        
        elif isinstance(expr, Primitive):
            # Handle special primitives that need evaluation context
            if expr.value == 'PYTHON_SUCC':
                return Primitive('PYTHON_ONE', '1')
            elif expr.value == 'PYTHON_ZERO':
                return Primitive('PYTHON_ZERO', '0')
            return expr
        
        else:
            return expr
    
    def apply_primitive(self, func: Primitive, arg: Expression, depth: int) -> Expression:
        """Apply built-in primitive functions"""
        arg_val = self.evaluate(arg, depth + 1)
        
        # Church numerals and arithmetic
        if func.value == 'SUCC':
            return self.church_succ(arg_val)
        elif func.value == 'PRED':
            return self.church_pred(arg_val)
        elif func.value == 'ISZERO':
            return self.church_iszero(arg_val)
        elif func.value == 'ADD':
            return self.church_add_partial(arg_val)
        elif func.value == 'MULT':
            return self.church_mult_partial(arg_val)
        elif func.value == 'RECURSION':
            return self.y_combinator(arg_val)
        elif func.value == 'PRINT':
            # Print the value and return it
            print(f"PRINT: {self.evaluator.interpreter.pretty_print(arg_val)}")
            return arg_val
        
        # For now, return application for unimplemented primitives
        return Application(func, arg_val)
    
    def church_succ(self, n: Expression) -> Expression:
        """Successor function for Church numerals"""
        # SUCC = λn.λf.λx.f (n f x)
        return Lambda('f', Lambda('x', 
            Application(Variable('f'), 
                Application(Application(n, Variable('f')), Variable('x')))))
    
    def church_pred(self, n: Expression) -> Expression:
        """Predecessor function for Church numerals"""
        # PRED = λn.λf.λx.n (λg.λh.h (g f)) (λu.x) (λu.u)
        # Simplified implementation using pairs
        return Lambda('f', Lambda('x', 
            Application(
                Application(
                    Application(n, 
                        Lambda('g', Lambda('h', 
                            Application(Variable('h'), 
                                Application(Variable('g'), Variable('f')))))),
                    Lambda('u', Variable('x'))),
                Lambda('u', Variable('u')))))
    
    def church_iszero(self, n: Expression) -> Expression:
        """Is-zero predicate for Church numerals"""
        # ISZERO = λn.n (λx.FALSE) TRUE
        false_expr = Lambda('x', Lambda('y', Variable('y')))  # FALSE
        true_expr = Lambda('x', Lambda('y', Variable('x')))   # TRUE
        return Application(Application(n, Lambda('x', false_expr)), true_expr)
    
    def church_add_partial(self, m: Expression) -> Expression:
        """Partial application of Church addition"""
        # ADD = λm.λn.λf.λx.m f (n f x)
        return Lambda('n', Lambda('f', Lambda('x',
            Application(
                Application(m, Variable('f')),
                Application(
                    Application(Variable('n'), Variable('f')),
                    Variable('x'))))))
    
    def church_mult_partial(self, m: Expression) -> Expression:
        """Partial application of Church multiplication"""
        # MULT = λm.λn.λf.m (n f)
        return Lambda('n', Lambda('f',
            Application(m, Application(Variable('n'), Variable('f')))))
    
    def y_combinator(self, f: Expression) -> Expression:
        """Y combinator for recursion"""
        # Y = λf.(λx.f (x x)) (λx.f (x x))
        xx_term = Lambda('x', Application(f, Application(Variable('x'), Variable('x'))))
        return Application(xx_term, xx_term)

# ============================================================================
# Built-in Church Encodings
# ============================================================================

def create_church_numeral(n: int) -> Expression:
    """Create Church numeral for integer n"""
    if n == 0:
        return Lambda('f', Lambda('x', Variable('x')))
    else:
        # Build f(f(...f(x)...)) with n applications of f
        body = Variable('x')
        for _ in range(n):
            body = Application(Variable('f'), body)
        return Lambda('f', Lambda('x', body))

def create_church_boolean(value: bool) -> Expression:
    """Create Church boolean"""
    if value:
        return Lambda('x', Lambda('y', Variable('x')))  # TRUE
    else:
        return Lambda('x', Lambda('y', Variable('y')))  # FALSE

# ============================================================================
# Main Interpreter
# ============================================================================

class SmileyInterpreter:
    """Main interpreter for Smiley language"""
    
    def __init__(self):
        self.evaluator = SmileyEvaluator()
        self.evaluator.interpreter = self  # Back-reference for printing
        self.setup_builtins()
    
    def setup_builtins(self):
        """Set up built-in values and functions"""
        # Church numerals - create them as proper lambda expressions
        self.evaluator.environment['0_num'] = create_church_numeral(0)
        self.evaluator.environment['1_num'] = create_church_numeral(1)
        self.evaluator.environment['2_num'] = create_church_numeral(2)
        self.evaluator.environment['3_num'] = create_church_numeral(3)
        self.evaluator.environment['4_num'] = create_church_numeral(4)
        self.evaluator.environment['5_num'] = create_church_numeral(5)
        
        # Church booleans
        self.evaluator.environment['true'] = create_church_boolean(True)
        self.evaluator.environment['false'] = create_church_boolean(False)
    
    def run(self, source: str) -> Expression:
        """Run Smiley source code"""
        try:
            # Tokenize
            tokenizer = SmileyTokenizer(source)
            tokens = tokenizer.tokenize()
            
            # Parse
            parser = SmileyParser(tokens)
            ast = parser.parse()
            
            # Evaluate
            result = self.evaluator.evaluate(ast)
            
            return result
            
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def church_numeral_to_int(self, expr: Expression, max_depth: int = 20) -> int:
        """Convert Church numeral to Python integer for display"""
        try:
            # Check if it's a lambda with the Church numeral structure
            if not isinstance(expr, Lambda):
                return -1
            
            # Church numeral should be λf.λx.f^n(x)
            if not isinstance(expr.body, Lambda):
                return -1
            
            f_param = expr.param
            x_param = expr.body.param
            body = expr.body.body
            
            # Count applications of f
            count = 0
            current = body
            
            # If body is just x, it's 0
            if isinstance(current, Variable) and current.name == x_param:
                return 0
            
            # Count nested applications of f
            while isinstance(current, Application) and count < max_depth:
                if (isinstance(current.func, Variable) and 
                    current.func.name == f_param):
                    count += 1
                    current = current.arg
                else:
                    break
            
            # Check if we ended with x
            if isinstance(current, Variable) and current.name == x_param:
                return count
            
            return -1  # Not a valid Church numeral
            
        except:
            return -1  # Could not convert
    
    def pretty_print(self, expr: Expression) -> str:
        """Pretty print expression for output"""
        # Try to convert Church numerals to integers
        if isinstance(expr, Lambda):
            num_val = self.church_numeral_to_int(expr)
            if num_val >= 0:
                return f"Church({num_val})"
            # Show the lambda structure for non-numerals
            return f"λ{expr.param}.{self.pretty_print(expr.body)}"
        elif isinstance(expr, Application):
            return f"({self.pretty_print(expr.func)} {self.pretty_print(expr.arg)})"
        elif isinstance(expr, Variable):
            return expr.name
        elif isinstance(expr, Primitive):
            return expr.name
        elif isinstance(expr, Binding):
            return f"let {expr.var} = {self.pretty_print(expr.value)} in {self.pretty_print(expr.body)}"
        else:
            return str(expr)

# ============================================================================
# Example Usage
# ============================================================================

def main():
    interpreter = SmileyInterpreter()
    
    print("🙂 Smiley Programming Language Interpreter 🙂")
    print("=" * 50)
    
    # Example 1: Simple lambda
    print("\nExample 1: Identity function")
    code1 = ":) :o -> :o :P"
    print(f"Code: {code1}")
    result1 = interpreter.run(code1)
    if result1:
        print(f"Result: {interpreter.pretty_print(result1)}")
    
    # Example 1.5: Test Church numerals directly
    print("\nExample 1.5: Direct Church numerals")
    code1_5 = "2_2"
    print(f"Code: {code1_5}")
    result1_5 = interpreter.run(code1_5)
    if result1_5:
        print(f"Result: {interpreter.pretty_print(result1_5)}")
    
    # Example 2: Function application with identity
    print("\nExample 2: Identity applied to 1")
    code2 = ":( :) :o -> :o :P 1_1 :P"
    print(f"Code: {code2}")
    result2 = interpreter.run(code2)
    if result2:
        print(f"Result: {interpreter.pretty_print(result2)}")
    
    # Example 3: Variable binding
    print("\nExample 3: Variable binding")
    code3 = ":D :o = 2_2 :P :o"
    print(f"Code: {code3}")
    result3 = interpreter.run(code3)
    if result3:
        print(f"Result: {interpreter.pretty_print(result3)}")
    
    # Example 4: Test successor function directly on a small number
    print("\nExample 4: Successor of 1")
    code4 = ":( +_+ 1_1 :P"
    print(f"Code: {code4}")
    result4 = interpreter.run(code4)
    if result4:
        print(f"Result: {interpreter.pretty_print(result4)}")
        print(f"Raw structure: {result4}")
    
    # Example 5: Simpler addition test
    print("\nExample 5: Addition test (1 + 1)")
    code5 = ":( :( /_/ 1_1 :P 1_1 :P"
    print(f"Code: {code5}")
    result5 = interpreter.run(code5)
    if result5:
        print(f"Result: {interpreter.pretty_print(result5)}")
        print(f"Raw structure: {result5}")
    
    print("\n" + "=" * 50)
    print("Debug: Let's see what Church numerals look like:")
    
    # Show raw Church numerals
    zero = create_church_numeral(0)
    one = create_church_numeral(1) 
    two = create_church_numeral(2)
    
    print(f"Church 0: {interpreter.pretty_print(zero)}")
    print(f"Church 1: {interpreter.pretty_print(one)}")
    print(f"Church 2: {interpreter.pretty_print(two)}")
    
    print("\nHappy coding with Smiley! 😊")

if __name__ == "__main__":
    main()

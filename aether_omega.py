#!/usr/bin/env python3
#!/usr/bin/env python3
"""Aether-Omega scalar compiler, SSA interpreter, and Rindler experiment."""

from dataclasses import dataclass, field
import math
import operator
import re
import sys
import time


# ---------------------------------------------------------------------
# Lexer and parser
# ---------------------------------------------------------------------

TOKEN = re.compile(
    r"(?P<space>\s+)"
    r"|(?P<comment>//[^\n]*)"
    r"|(?P<number>(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"
    r"|(?P<id>[A-Za-z_][A-Za-z_0-9]*)"
    r"|(?P<op>->|<=|>=|==|!=|&&|\|\||[+\-*/<>=!;,():{}])"
)


def lex(source):
    out = []
    pos = 0
    while pos < len(source):
        match = TOKEN.match(source, pos)
        if match is None:
            raise SyntaxError(
                f"invalid character at offset {pos}: {source[pos]!r}"
            )
        kind = match.lastgroup
        if kind not in ("space", "comment"):
            out.append((kind, match.group(), pos))
        pos = match.end()
    out.append(("eof", "<eof>", len(source)))
    return out


@dataclass
class Function:
    name: str
    params: list
    result: str
    declarations: list
    body: list
    returned: tuple
    types: dict = field(default_factory=dict)


class Parser:
    PRECEDENCE = {
        "||": 1,
        "&&": 2,
        "==": 3, "!=": 3,
        "<": 4, "<=": 4, ">": 4, ">=": 4,
        "+": 5, "-": 5,
        "*": 6, "/": 6,
    }

    RESERVED = {
        "fn", "var", "return", "if", "else", "while",
        "true", "false", "real", "bool",
    }

    def __init__(self, source):
        self.tokens = lex(source)
        self.i = 0

    def peek(self):
        return self.tokens[self.i][1]

    def take(self):
        token = self.tokens[self.i]
        self.i += 1
        return token

    def accept(self, text):
        if self.peek() == text:
            self.take()
            return True
        return False

    def expect(self, text):
        if not self.accept(text):
            token = self.tokens[self.i]
            raise SyntaxError(
                f"expected {text!r}, got {token[1]!r} at {token[2]}"
            )

    def identifier(self):
        token = self.take()
        if token[0] != "id" or token[1] in self.RESERVED:
            raise SyntaxError(f"expected identifier at {token[2]}")
        return token[1]

    def parse_type(self):
        text = self.take()[1]
        if text not in ("real", "bool"):
            raise SyntaxError(f"unsupported prototype type: {text}")
        return text

    def expression(self, minimum=1):
        if self.peek() in ("-", "!"):
            op = self.take()[1]
            left = ("unary", op, self.expression(7))
        elif self.accept("("):
            left = self.expression()
            self.expect(")")
        elif self.tokens[self.i][0] == "number":
            left = ("const", float(self.take()[1]), "real")
        elif self.peek() in ("true", "false"):
            left = ("const", self.take()[1] == "true", "bool")
        else:
            name = self.identifier()
            if self.accept("("):
                args = []
                if self.peek() != ")":
                    args.append(self.expression())
                    while self.accept(","):
                        args.append(self.expression())
                self.expect(")")
                left = ("call", name, tuple(args))
            else:
                left = ("name", name)

        while self.PRECEDENCE.get(self.peek(), 0) >= minimum:
            op = self.take()[1]
            precedence = self.PRECEDENCE[op]
            right = self.expression(precedence + 1)
            left = ("binary", op, left, right)
        return left

    def block(self):
        self.expect("{")
        statements = []
        while self.peek() != "}":
            if self.peek() == "<eof>":
                raise SyntaxError("unterminated block")
            statements.append(self.statement())
        self.expect("}")
        return statements

    def statement(self):
        if self.accept("if"):
            condition = self.expression()
            yes = self.block()
            no = self.block() if self.accept("else") else []
            return ("if", condition, yes, no)

        if self.accept("while"):
            condition = self.expression()
            return ("while", condition, self.block())

        name = self.identifier()
        self.expect("=")
        value = self.expression()
        self.expect(";")
        return ("assign", name, value)

    def function(self):
        self.expect("fn")
        name = self.identifier()
        self.expect("(")
        params = []

        if self.peek() != ")":
            while True:
                parameter = self.identifier()
                self.expect(":")
                params.append((parameter, self.parse_type()))
                if not self.accept(","):
                    break

        self.expect(")")
        self.expect("->")
        result = self.parse_type()
        self.expect("{")

        declarations = []
        while self.accept("var"):
            variable = self.identifier()
            self.expect(":")
            typ = self.parse_type()
            self.expect("=")
            value = self.expression()
            self.expect(";")
            declarations.append((variable, typ, value))

        body = []
        while self.peek() != "return":
            if self.peek() in ("}", "<eof>"):
                raise SyntaxError("function requires a final return")
            body.append(self.statement())

        self.expect("return")
        returned = self.expression()
        self.expect(";")
        self.expect("}")

        return Function(
            name, params, result, declarations, body, returned
        )

    def program(self):
        functions = []
        while self.peek() != "<eof>":
            functions.append(self.function())
        if not functions:
            raise SyntaxError("empty program")
        return functions


# ---------------------------------------------------------------------
# Type checking and semantic analysis
# ---------------------------------------------------------------------

BUILTINS = {
    "exp": math.exp,
    "log": math.log,
    "sqrt": math.sqrt,
    "abs": abs,
}


class Checker:
    def __init__(self, functions):
        self.functions = {}
        self.signatures = {
            name: (("real",), "real") for name in BUILTINS
        }
        self.edges = {}
        self.current = None

        for function in functions:
            if function.name in self.signatures:
                raise TypeError(f"duplicate/reserved function {function.name}")
            self.functions[function.name] = function
            self.signatures[function.name] = (
                tuple(typ for _, typ in function.params),
                function.result,
            )
            self.edges[function.name] = set()

    def expression(self, node, environment):
        kind = node[0]

        if kind == "const":
            return node[2]

        if kind == "name":
            if node[1] not in environment:
                raise TypeError(f"unbound variable {node[1]}")
            return environment[node[1]]

        if kind == "unary":
            typ = self.expression(node[2], environment)
            wanted = "real" if node[1] == "-" else "bool"
            if typ != wanted:
                raise TypeError(f"{node[1]} requires {wanted}")
            return wanted

        if kind == "binary":
            op = node[1]
            left = self.expression(node[2], environment)
            right = self.expression(node[3], environment)

            if op in ("+", "-", "*", "/"):
                if left != "real" or right != "real":
                    raise TypeError(f"{op} requires real operands")
                return "real"

            if op in ("<", "<=", ">", ">="):
                if left != "real" or right != "real":
                    raise TypeError(f"{op} requires real operands")
                return "bool"

            if op in ("==", "!="):
                if left != right:
                    raise TypeError("equality operands have different types")
                return "bool"

            if left != "bool" or right != "bool":
                raise TypeError(f"{op} requires bool operands")
            return "bool"

        if kind == "call":
            name, args = node[1], node[2]
            if name not in self.signatures:
                raise TypeError(f"unknown function {name}")
            expected, returned = self.signatures[name]
            actual = tuple(self.expression(arg, environment) for arg in args)
            if actual != expected:
                raise TypeError(
                    f"{name}: expected {expected}, received {actual}"
                )
            if name in self.functions:
                self.edges[self.current].add(name)
            return returned

        raise TypeError(f"unknown expression kind {kind}")

    def statements(self, statements, environment):
        for statement in statements:
            kind = statement[0]

            if kind == "assign":
                name = statement[1]
                if name not in environment:
                    raise TypeError(f"assignment to undeclared variable {name}")
                actual = self.expression(statement[2], environment)
                if actual != environment[name]:
                    raise TypeError(f"assignment changes type of {name}")

            elif kind == "if":
                if self.expression(statement[1], environment) != "bool":
                    raise TypeError("if condition must be bool")
                self.statements(statement[2], environment)
                self.statements(statement[3], environment)

            elif kind == "while":
                if self.expression(statement[1], environment) != "bool":
                    raise TypeError("while condition must be bool")
                self.statements(statement[2], environment)

            else:
                raise TypeError(f"unknown statement kind {kind}")

    def check(self):
        for name, function in self.functions.items():
            self.current = name
            environment = {}

            for variable, typ in function.params:
                if variable in environment:
                    raise TypeError(f"duplicate parameter {variable}")
                environment[variable] = typ

            for variable, typ, value in function.declarations:
                if variable in environment:
                    raise TypeError(f"duplicate local {variable}")
                if self.expression(value, environment) != typ:
                    raise TypeError(f"initializer type mismatch for {variable}")
                environment[variable] = typ

            self.statements(function.body, environment)
            if self.expression(function.returned, environment) != function.result:
                raise TypeError(f"return type mismatch in {name}")
            function.types = environment

        visiting = set()
        visited = set()

        def visit(name):
            if name in visiting:
                raise TypeError("recursive call graph is unsupported")
            if name in visited:
                return
            visiting.add(name)
            for child in self.edges[name]:
                visit(child)
            visiting.remove(name)
            visited.add(name)

        for name in self.functions:
            visit(name)

        return self.functions


# ---------------------------------------------------------------------
# SSA representation and lowering
# ---------------------------------------------------------------------

@dataclass
class Phi:
    destination: str
    typ: str
    incoming: list


@dataclass
class Instruction:
    destination: str
    operation: str
    typ: str
    args: tuple


@dataclass
class Block:
    name: str
    phis: list = field(default_factory=list)
    instructions: list = field(default_factory=list)
    terminator: tuple = ()


@dataclass
class IRFunction:
    name: str
    params: list
    result: str
    blocks: dict
    register_types: dict


class Lowerer:
    def __init__(self, function, signatures):
        self.function = function
        self.signatures = signatures
        self.blocks = {}
        self.register_types = {}
        self.register_count = 0
        self.block_count = 0
        self.current = self.new_block()
        self.environment = {}

        for name, typ in function.params:
            register = "%" + name
            self.register_types[register] = typ
            self.environment[name] = register

    def new_register(self, typ):
        # Generated names cannot collide with source identifiers.
        name = f"%v.{self.register_count}"
        self.register_count += 1
        self.register_types[name] = typ
        return name

    def new_block(self):
        name = f"b{self.block_count}"
        self.block_count += 1
        self.blocks[name] = Block(name)
        return name

    def emit(self, operation, typ, args):
        destination = self.new_register(typ)
        self.blocks[self.current].instructions.append(
            Instruction(destination, operation, typ, tuple(args))
        )
        return destination

    def expression(self, node):
        kind = node[0]

        if kind == "const":
            return self.emit("const", node[2], (node[1],))

        if kind == "name":
            return self.environment[node[1]]

        if kind == "unary":
            value = self.expression(node[2])
            typ = "real" if node[1] == "-" else "bool"
            return self.emit("neg" if node[1] == "-" else "not", typ, (value,))

        if kind == "binary":
            left = self.expression(node[2])
            right = self.expression(node[3])
            typ = "real" if node[1] in ("+", "-", "*", "/") else "bool"
            return self.emit(node[1], typ, (left, right))

        if kind == "call":
            args = tuple(self.expression(arg) for arg in node[2])
            typ = self.signatures[node[1]][1]
            return self.emit("call", typ, (node[1], args))

        raise RuntimeError("invalid typed expression")

    def statements(self, statements):
        for statement in statements:
            kind = statement[0]

            if kind == "assign":
                value = self.expression(statement[2])
                self.environment[statement[1]] = value

            elif kind == "if":
                condition = self.expression(statement[1])
                start_environment = dict(self.environment)
                yes = self.new_block()
                no = self.new_block()
                join = self.new_block()

                self.blocks[self.current].terminator = (
                    "cbr", condition, yes, no
                )

                self.current = yes
                self.environment = dict(start_environment)
                self.statements(statement[2])
                yes_end = self.current
                yes_environment = dict(self.environment)
                self.blocks[yes_end].terminator = ("br", join)

                self.current = no
                self.environment = dict(start_environment)
                self.statements(statement[3])
                no_end = self.current
                no_environment = dict(self.environment)
                self.blocks[no_end].terminator = ("br", join)

                self.current = join
                merged = {}

                for name in start_environment:
                    a = yes_environment[name]
                    b = no_environment[name]
                    if a == b:
                        merged[name] = a
                    else:
                        typ = self.function.types[name]
                        destination = self.new_register(typ)
                        self.blocks[join].phis.append(
                            Phi(destination, typ, [(yes_end, a), (no_end, b)])
                        )
                        merged[name] = destination

                self.environment = merged

            elif kind == "while":
                predecessor = self.current
                before = dict(self.environment)
                header = self.new_block()
                body = self.new_block()
                exit_block = self.new_block()

                self.blocks[predecessor].terminator = ("br", header)

                header_environment = {}
                pending = {}

                for name, old_register in before.items():
                    typ = self.function.types[name]
                    destination = self.new_register(typ)
                    phi = Phi(
                        destination, typ, [(predecessor, old_register)]
                    )
                    self.blocks[header].phis.append(phi)
                    pending[name] = phi
                    header_environment[name] = destination

                self.current = header
                self.environment = dict(header_environment)
                condition = self.expression(statement[1])
                self.blocks[header].terminator = (
                    "cbr", condition, body, exit_block
                )

                self.current = body
                self.environment = dict(header_environment)
                self.statements(statement[2])
                body_end = self.current
                back_environment = dict(self.environment)
                self.blocks[body_end].terminator = ("br", header)

                for name, phi in pending.items():
                    phi.incoming.append((body_end, back_environment[name]))

                self.current = exit_block
                self.environment = header_environment

            else:
                raise RuntimeError("invalid typed statement")

    def lower(self):
        for name, typ, value in self.function.declarations:
            self.environment[name] = self.expression(value)

        self.statements(self.function.body)
        returned = self.expression(self.function.returned)
        self.blocks[self.current].terminator = ("ret", returned)

        return IRFunction(
            self.function.name,
            list(self.function.params),
            self.function.result,
            self.blocks,
            self.register_types,
        )


def compile_source(source):
    ast = Parser(source).program()
    checker = Checker(ast)
    functions = checker.check()
    return {
        name: Lowerer(function, checker.signatures).lower()
        for name, function in functions.items()
    }


# ---------------------------------------------------------------------
# LLVM-like text generation
# ---------------------------------------------------------------------

def llvm_type(typ):
    return "double" if typ == "real" else "i1"


def ir_text(program):
    lines = [
        "; Aether-Omega SSA",
        "; LLVM-like educational dialect; 'const' is a pseudo-instruction.",
        "; This file is not claimed to be accepted by LLVM.",
    ]

    for name in BUILTINS:
        lines.append(f"declare double @{name}(double)")

    arithmetic = {"+": "fadd", "-": "fsub", "*": "fmul", "/": "fdiv"}
    comparison = {
        "<": "olt", "<=": "ole", ">": "ogt", ">=": "oge",
        "==": "oeq", "!=": "une",
    }

    for function in program.values():
        parameters = ", ".join(
            f"{llvm_type(typ)} %{name}" for name, typ in function.params
        )
        lines.append(
            f"\ndefine {llvm_type(function.result)} "
            f"@{function.name}({parameters}) {{"
        )

        def typed(register):
            return (
                f"{llvm_type(function.register_types[register])} {register}"
            )

        for block in function.blocks.values():
            lines.append(f"{block.name}:")

            for phi in block.phis:
                incoming = ", ".join(
                    f"[ {register}, %{predecessor} ]"
                    for predecessor, register in phi.incoming
                )
                lines.append(
                    f"  {phi.destination} = phi {llvm_type(phi.typ)} {incoming}"
                )

            for ins in block.instructions:
                op = ins.operation
                args = ins.args

                if op == "const":
                    value = args[0]
                    literal = (
                        "true" if value else "false"
                    ) if ins.typ == "bool" else repr(value)
                    rhs = f"const {llvm_type(ins.typ)} {literal}"

                elif op == "call":
                    callee, registers = args
                    arguments = ", ".join(typed(r) for r in registers)
                    rhs = (
                        f"call {llvm_type(ins.typ)} "
                        f"@{callee}({arguments})"
                    )

                elif op in arithmetic:
                    rhs = (
                        f"{arithmetic[op]} double {args[0]}, {args[1]}"
                    )

                elif op in comparison:
                    input_type = function.register_types[args[0]]
                    if input_type == "bool":
                        predicate = "eq" if op == "==" else "ne"
                        rhs = f"icmp {predicate} i1 {args[0]}, {args[1]}"
                    else:
                        rhs = (
                            f"fcmp {comparison[op]} double "
                            f"{args[0]}, {args[1]}"
                        )

                elif op == "neg":
                    rhs = f"fneg double {args[0]}"

                elif op == "not":
                    rhs = f"xor i1 {args[0]}, true"

                elif op in ("&&", "||"):
                    opcode = "and" if op == "&&" else "or"
                    rhs = f"{opcode} i1 {args[0]}, {args[1]}"

                else:
                    raise RuntimeError(f"cannot print operation {op}")

                lines.append(f"  {ins.destination} = {rhs}")

            term = block.terminator
            if term[0] == "br":
                lines.append(f"  br label %{term[1]}")
            elif term[0] == "cbr":
                lines.append(
                    f"  br i1 {term[1]}, "
                    f"label %{term[2]}, label %{term[3]}"
                )
            elif term[0] == "ret":
                lines.append(f"  ret {typed(term[1])}")
            else:
                raise RuntimeError("unterminated SSA block")

        lines.append("}")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------
# SSA interpreter
# ---------------------------------------------------------------------

BINARY = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
    "==": operator.eq,
    "!=": operator.ne,
    "&&": operator.and_,
    "||": operator.or_,
}


class VM:
    def __init__(self, program, fuel=50_000_000):
        self.program = program
        self.fuel = fuel

    def tick(self):
        self.fuel -= 1
        if self.fuel < 0:
            raise RuntimeError("execution fuel exhausted")

    def call(self, name, *arguments):
        if name in BUILTINS:
            self.tick()
            return float(BUILTINS[name](*arguments))

        if name not in self.program:
            raise RuntimeError(f"unknown IR function {name}")

        function = self.program[name]
        if len(arguments) != len(function.params):
            raise TypeError("host call has wrong arity")

        registers = {}
        for (parameter, typ), value in zip(function.params, arguments):
            if typ == "bool":
                if type(value) is not bool:
                    raise TypeError("host bool parameter requires bool")
                registers["%" + parameter] = value
            else:
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise TypeError("host real parameter requires a number")
                registers["%" + parameter] = float(value)

        current = next(iter(function.blocks))
        predecessor = None

        while True:
            self.tick()
            block = function.blocks[current]

            # Phi assignments are simultaneous, including loop-carried swaps.
            updates = {}
            for phi in block.phis:
                matches = [
                    register for pred, register in phi.incoming
                    if pred == predecessor
                ]
                if len(matches) != 1:
                    raise RuntimeError("invalid phi predecessor")
                updates[phi.destination] = registers[matches[0]]
            registers.update(updates)

            for ins in block.instructions:
                self.tick()
                op = ins.operation

                if op == "const":
                    value = ins.args[0]
                elif op == "call":
                    callee, refs = ins.args
                    value = self.call(
                        callee, *(registers[ref] for ref in refs)
                    )
                elif op == "neg":
                    value = -registers[ins.args[0]]
                elif op == "not":
                    value = not registers[ins.args[0]]
                else:
                    value = BINARY[op](
                        registers[ins.args[0]], registers[ins.args[1]]
                    )

                registers[ins.destination] = value

            term = block.terminator

            if term[0] == "ret":
                return registers[term[1]]

            old = current
            if term[0] == "br":
                current = term[1]
            elif term[0] == "cbr":
                current = term[2] if registers[term[1]] else term[3]
            else:
                raise RuntimeError("invalid terminator")
            predecessor = old


# ---------------------------------------------------------------------
# Aether-Omega physics source
# ---------------------------------------------------------------------

PHYSICS = r"""
fn world_t(rho: real, eta: real) -> real {
    return rho * (exp(eta) - exp(-eta)) / 2;
}

fn world_x(rho: real, eta: real) -> real {
    return rho * (exp(eta) + exp(-eta)) / 2;
}

// RK4 integration of d(rho)/d(eta) = direction * rho.
// The auxiliary characteristic is integrated for all n steps over [0,8].
// Only its first detector crossing is interpreted as physical reception.
fn flight(n: real, direction: real) -> real {
    var h: real = 8 / n;
    var rho: real = 1;
    var target: real = 2;
    var next: real = 0;
    var k1: real = 0;
    var k2: real = 0;
    var k3: real = 0;
    var k4: real = 0;
    var answer: real = -1;
    var fraction: real = 0;
    var found: bool = false;
    var i: real = 0;

    if direction < 0 {
        rho = 2;
        target = 1;
    }

    while i < n {
        k1 = direction * rho;
        k2 = direction * (rho + h * k1 / 2);
        k3 = direction * (rho + h * k2 / 2);
        k4 = direction * (rho + h * k3);

        next = rho + h * (k1 + 2 * k2 + 2 * k3 + k4) / 6;

        if !found {
            if direction * (next - target) >= 0 {
                fraction = log(target / rho) / log(next / rho);
                answer = (i + fraction) * h;
                found = true;
            }
        }

        rho = next;
        i = i + 1;
    }

    return answer;
}

fn frequency(delay: real, direction: real) -> real {
    return exp(-direction * delay);
}

fn lag(eta: real, delay: real, direction: real) -> real {
    var emitter: real = 1;
    var receiver: real = 2;

    if direction < 0 {
        emitter = 2;
        receiver = 1;
    }

    return world_t(receiver, eta + delay) - world_t(emitter, eta);
}

fn receiver_tau(eta: real, delay: real, direction: real) -> real {
    var receiver: real = 2;

    if direction < 0 {
        receiver = 1;
    }

    return receiver * (eta + delay);
}

// Trace the continuum communication law on n emission intervals.
// Return a coordinate-normalized null residual.
fn sweep(n: real, delay: real, direction: real) -> real {
    var emitter: real = 1;
    var receiver: real = 2;
    var eta: real = 0;
    var te: real = 0;
    var xe: real = 0;
    var tr: real = 0;
    var xr: real = 0;
    var residual: real = 0;
    var maximum: real = 0;
    var i: real = 0;

    if direction < 0 {
        emitter = 2;
        receiver = 1;
    }

    while i <= n {
        eta = 2 * i / n;
        te = world_t(emitter, eta);
        xe = world_x(emitter, eta);
        tr = world_t(receiver, eta + delay);
        xr = world_x(receiver, eta + delay);

        residual = abs((xr - xe) - direction * (tr - te));
        residual = residual / (
            1 + abs(te) + abs(xe) + abs(tr) + abs(xr)
        );

        if residual > maximum {
            maximum = residual;
        }

        i = i + 1;
    }

    return maximum;
}

// Exact characteristic used only to draw photon positions.
fn photon_rho(age: real, direction: real) -> real {
    var start: real = 1;

    if direction < 0 {
        start = 2;
    }

    return start * exp(direction * age);
}

fn phi_swap(n: real) -> real {
    var a: real = 1;
    var b: real = 2;
    var temp: real = 0;
    var i: real = 0;

    while i < n {
        temp = a;
        a = b;
        b = temp;
        i = i + 1;
    }

    return a;
}
"""


# ---------------------------------------------------------------------
# Validation and reporting
# ---------------------------------------------------------------------

def compiler_tests(program):
    vm = VM(program)

    if vm.call("phi_swap", 3) != 2:
        raise AssertionError("loop phi swap test failed")
    if vm.call("phi_swap", 4) != 1:
        raise AssertionError("even loop phi swap test failed")

    invalid_sources = [
        "fn f() -> real { return true; }",
        "fn f() -> real { var x: real = y; return x; }",
        "fn f() -> real { return f(); }",
        "fn f() -> real { var x: real = 1; x = false; return x; }",
    ]

    for source in invalid_sources:
        try:
            compile_source(source)
        except (SyntaxError, TypeError):
            continue
        raise AssertionError("invalid program was accepted")


def convergence(vm):
    exact = math.log(2.0)
    measurements = {}

    print("\nCONVERGENCE: RK4 plus logarithmic event interpolation")
    print("steps  direction     delay                  abs error       ratio")

    for direction in (1.0, -1.0):
        previous_error = None

        for n in (512, 1024, 2048):
            delay = vm.call("flight", n, direction)
            error = abs(delay - exact)
            ratio = (
                previous_error / error
                if previous_error is not None and error != 0
                else None
            )
            ratio_text = "-" if ratio is None else f"{ratio:.4f}"

            print(
                f"{n:5d} {direction:+10.0f} "
                f"{delay:.16f}  {error:.6e}  {ratio_text}"
            )

            if not (0 < delay < 8):
                raise AssertionError("detector crossing was not found")
            if error >= 1e-8:
                raise AssertionError("flight time is insufficiently accurate")

            if ratio is not None and not (8 < ratio < 24):
                raise AssertionError(
                    "observed convergence is inconsistent with order four"
                )

            measurements[(n, direction)] = delay
            previous_error = error

    return measurements


def numerical_report(vm, measurements):
    print("\nOBSERVABLES FROM EXECUTED SSA, using 512 propagation steps")
    print("eta_e  dir  tau_e       tau_r          delta_t         nu_r/nu_e")

    for eta in (0.0, 0.5, 1.0, 1.5, 2.0):
        for direction in (1.0, -1.0):
            delay = measurements[(512, direction)]
            emitter = 1.0 if direction > 0 else 2.0
            tau_e = emitter * eta
            tau_r = vm.call("receiver_tau", eta, delay, direction)
            travel = vm.call("lag", eta, delay, direction)
            ratio = vm.call("frequency", delay, direction)

            exact_travel = (
                1.5 * math.exp(eta)
                if direction > 0
                else 0.75 * math.exp(-eta)
            )
            exact_ratio = 0.5 if direction > 0 else 2.0

            if abs(travel - exact_travel) > 2e-8:
                raise AssertionError("coordinate travel-time validation failed")
            if abs(ratio - exact_ratio) > 2e-9:
                raise AssertionError("frequency validation failed")

            print(
                f"{eta:5.2f} {direction:+4.0f} "
                f"{tau_e:10.6f} {tau_r:13.9f} "
                f"{travel:14.9f} {ratio:13.10f}"
            )

    print("\n512-interval emission sweeps over eta_e in [0,2]:")
    for direction in (1.0, -1.0):
        delay = measurements[(512, direction)]
        residual = vm.call("sweep", 512, delay, direction)
        print(
            f"direction {direction:+.0f}: "
            f"maximum normalized null residual = {residual:.6e}"
        )
        if residual > 2e-9:
            raise AssertionError("null-consistency validation failed")


def frequency_plots(vm, measurements):
    print("\nFREQUENCY RATIO VERSUS EMITTER PROPER TIME")

    for direction, end in ((1.0, 2.0), (-1.0, 4.0)):
        delay = measurements[(512, direction)]
        values = [
            vm.call("frequency", delay, direction) for _ in range(41)
        ]
        mean = sum(values) / len(values)
        title = "A -> B" if direction > 0 else "B -> A"

        print(f"\n{title}; sampled ratio = {mean:.10f}")
        print(f"{mean:5.2f} |" + "*" * 41)
        print("     +-----------------------------------------> tau_e")
        print(f"      0{' ' * 36}{end:.1f}")


def moving_strip(vm, eta):
    # Highlight the newest bidirectional pulse pair.
    # New highlighted pairs are emitted at eta = 0, 0.8, 1.6.
    launch = 0.8 * math.floor((eta + 1e-12) / 0.8)
    age = eta - launch
    row = ["-"] * 21

    if age > 1e-12:
        for direction, symbol in ((1.0, ">"), (-1.0, "<")):
            rho = vm.call("photon_rho", age, direction)
            column = max(0, min(20, round(20 * (rho - 1))))
            row[column] = symbol

    row[0] = "A"
    row[20] = "B"
    return "".join(row)


def minkowski_frame(vm, eta):
    # Orthographic view of (x,y,t), with z suppressed.
    # y is zero for this experiment; it remains an explicit depth axis.
    width, height = 49, 17
    xmax, tmax = 8.0, 8.0
    grid = [[" "] * width for _ in range(height)]

    def put(x, y, t, symbol):
        projected_x = x + 0.35 * y
        projected_t = t + 0.20 * y
        column = round(projected_x / xmax * (width - 1))
        row = height - 1 - round(projected_t / tmax * (height - 1))
        if 0 <= row < height and 0 <= column < width:
            grid[row][column] = symbol

    # Ship histories.
    for j in range(41):
        past = eta * j / 40
        for rho in (1.0, 2.0):
            put(
                vm.call("world_x", rho, past),
                0.0,
                vm.call("world_t", rho, past),
                ".",
            )

    # Samples of continuous communication: pairs emitted every 0.2 in eta.
    count = int(math.floor((eta + 1e-12) / 0.2))
    exact_delay = math.log(2.0)

    for k in range(count + 1):
        launch = 0.2 * k
        age = eta - launch
        if age < -1e-12 or age > exact_delay + 1e-12:
            continue

        for direction, symbol in ((1.0, ">"), (-1.0, "<")):
            rho = vm.call("photon_rho", max(0.0, age), direction)
            put(
                vm.call("world_x", rho, eta),
                0.0,
                vm.call("world_t", rho, eta),
                symbol,
            )

    # Endpoint labels have priority over photons emitted at that instant.
    for rho, symbol in ((1.0, "A"), (2.0, "B")):
        put(
            vm.call("world_x", rho, eta),
            0.0,
            vm.call("world_t", rho, eta),
            symbol,
        )

    lines = [
        f"eta = {eta:.1f}; Minkowski viewport, x in [0,8], t in [0,8]",
        "t ^",
    ]
    lines.extend("  |" + "".join(row) for row in grid)
    lines.append("  +" + "-" * width + "> x")
    lines.append(" /")
    lines.append("y   (all displayed events have y=z=0)")
    lines.append("co-moving rho slice: " + moving_strip(vm, eta))
    return "\n".join(lines)


def animate(vm, realtime):
    print("\nTEN SEQUENTIAL SPACETIME FRAMES")
    print("Each frame is a common Rindler-eta slice, not a common Minkowski-t slice.")

    for frame in range(10):
        eta = frame * 0.2
        if realtime:
            print("\x1b[2J\x1b[H", end="")
        print(f"\nFRAME {frame:02d}")
        print(minkowski_frame(vm, eta))
        if realtime:
            sys.stdout.flush()
            time.sleep(0.12)


def main():
    program = compile_source(PHYSICS)
    compiler_tests(program)

    text = ir_text(program)
    with open("aether_demo.ll", "w", encoding="utf-8") as handle:
        handle.write(text)

    blocks = sum(len(function.blocks) for function in program.values())
    phis = sum(
        len(block.phis)
        for function in program.values()
        for block in function.blocks.values()
    )

    print("Aether-Omega scalar compilation succeeded.")
    print(f"Compiled functions: {len(program)}")
    print(f"SSA blocks: {blocks}; phi nodes: {phis}")
    print("LLVM-like IR written to aether_demo.ll")
    print("Compiler rejection and loop-phi tests passed.")

    vm = VM(program)
    measurements = convergence(vm)
    numerical_report(vm, measurements)
    frequency_plots(vm, measurements)
    animate(vm, "--animate" in sys.argv)

    print("\nAll runtime validation checks passed.")
    print(f"Remaining interpreter fuel: {vm.fuel}")


if __name__ == "__main__":
    main()

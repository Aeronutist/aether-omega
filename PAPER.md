# Aether-Ω: Language Design and a Scalar SSA Prototype for Rindler Communication

## Abstract

## Abstract

We present Aether-Ω, a proposed language architecture for parallel,
differentiable, geometry-aware, and quantum-classical computation,
together with an executable scalar compiler prototype.

The implemented subset provides lexical analysis, parsing, scalar type
checking, structured-control-flow lowering to static single assignment
form, LLVM-like textual rendering, and execution through an SSA
interpreter. The broader tensor, automatic-differentiation, capability,
verification, accelerator, and quantum facilities are specified design
proposals rather than implemented backends.

The application models bidirectional light communication between two
uniformly accelerated observers in the same Born-rigid Rindler
congruence in flat Minkowski spacetime. Numerical integration of radial
null characteristics is compared with exact reception-time and
frequency-ratio formulas. The event-time method has fourth-order
discretization error in exact arithmetic.

A Streamlit interface exposes numerical tables, convergence results,
generated IR, execution logs, and ASCII spacetime frames. Analytic
reference values are distinguished from captured execution results.
The work is an educational research prototype, not a production
compiler, a machine-verified implementation, or a simulation of
dynamical spacetime.

A central physical point is that the Rindler gravitational redshift and the inertial-frame Doppler shift are **two descriptions of the same frequency ratio**. Multiplying them as independent corrections would double-count the effect.

### Execution provenance and scope

No code-execution tool is available in this conversation. Therefore:

- The code below is a complete runnable artifact, not a claimed execution transcript.
- Numerical values printed in this document are **analytic reference values**.
- The supplied program executes the compiler, interpreter, numerical simulation, convergence tests, and visualization when run.
- The prototype implements the explicitly identified scalar language subset. Tensor, geometry, autodiff, capability, and quantum facilities are specified language features, **not falsely presented as implemented Python backends**.

Save the code block in §5 as `aether_omega.py` and run:

```bash
python3 aether_omega.py
```

For terminal animation:

```bash
python3 aether_omega.py --animate
```

Python 3.10 or later is sufficient.

---

## 1. Introduction

Scientific programming often combines several incompatible computational models:

1. Scalar and tensor numerical computation.
2. Automatic differentiation.
3. Differential geometry.
4. Distributed or heterogeneous execution.
5. Quantum state manipulation.
6. Formal specifications.
7. Restricted access to external resources.

Aether-Ω separates three concerns:

- **Mathematical meaning:** pure expressions, tensors, differentiation, and geometry.
- **Resource authority:** explicit capabilities for accelerators, I/O, and external state.
- **Execution strategy:** compiler-selected scheduling of independent operations.

The language does not promise that arbitrary programs can be parallelized, differentiated, verified, or accelerated quantum mechanically. Instead, each operation has a precise typing and effect contract.

The compiler artifact demonstrates the essential executable path:

\[
\text{source}
\rightarrow \text{tokens}
\rightarrow \text{AST}
\rightarrow \text{typed AST}
\rightarrow \text{SSA}
\rightarrow
\begin{cases}
\text{LLVM-like text},\\
\text{SSA interpreter}.
\end{cases}
\]

The physics application was selected because it has exact reference solutions, nontrivial coordinate transformations, horizon structure, and experimentally meaningful observables.

---

# 2. Language Design

## 2.1 Design principles

Aether-Ω uses the following rules.

### Implicit parallelism

Pure independent expressions may execute concurrently. Tensor operations define elementwise or reduction semantics without prescribing a thread layout.

A backend may select:

- CPU scalar or SIMD execution;
- CPU work stealing;
- GPU kernels;
- an authorized quantum backend for explicitly quantum computations.

“Implicit quantum parallelism” does **not** mean automatically translating arbitrary classical functions into advantageous quantum algorithms. It means scheduling independent quantum circuits and eligible quantum kernels alongside classical work.

### Native differentiation

Differentiation is defined on typed pure functions:

- `jvp` provides forward-mode directional derivatives.
- `grad` provides reverse-mode gradients of scalar-valued functions.
- Reverse mode uses a compiler-managed tape or a recomputation schedule.
- Mutation is functionalized before differentiation.
- Measurement and ordinary stochastic sampling are not pathwise differentiable by default.

### Geometry-aware values

A coordinate event, tangent, covector, and metric are distinct types. For example:

```text
Event[Minkowski]
Tangent[Minkowski]
Covector[Minkowski]
Metric[Minkowski]
```

A tangent in one coordinate frame cannot silently be used in another.

### Memory safety

Ordinary mathematical values have value semantics. Compiler-generated buffers are uniquely owned or immutably shared.

Quantum registers and capabilities are affine resources. A quantum register cannot be copied. Resource borrows cannot escape their calls.

### Verification

Contracts are mathematical specifications, not comments:

```text
requires(condition)
ensures(condition)
invariant(condition)
```

A compiler operating in verified mode must prove the relevant obligations or reject the program. Checked mode retains executable contract checks.

### Capability security

Possessing a value of type `Cap[Quantum]` authorizes quantum-backend use; possessing `Cap[IO]` authorizes output. Programs cannot manufacture capabilities.

Pure arithmetic does not require an external-resource capability. Accelerator dispatch, filesystem access, networking, and hardware measurement do.

---

## 2.2 Complete surface grammar

The following grammar defines the surface language for this design revision. Whitespace and `//` comments are insignificant outside tokens.

`{ X }` means repetition, `[ X ]` means optional syntax, and quoted characters are literal tokens.

```ebnf
program       = { function } ;

function      = "fn", identifier, "(",
                [ parameter, { ",", parameter } ],
                ")", "->", type,
                [ effects ],
                { precondition | postcondition },
                "{", { declaration }, { statement },
                "return", expression, ";", "}" ;

parameter     = identifier, ":", parameter_type ;
parameter_type = type | "view", type | "edit", type ;

effects       = "!", "{",
                [ effect, { ",", effect } ],
                "}" ;
effect        = "compute" | "quantum" | "io" ;

precondition  = "requires", "(", expression, ")" ;
postcondition = "ensures", "(", expression, ")" ;
loop_contract = "invariant", "(", expression, ")" ;

declaration   = "var", identifier, ":", type,
                "=", expression, ";" ;

statement     = assignment
              | conditional
              | loop
              | expression, ";" ;

assignment    = identifier, "=", expression, ";" ;

conditional   = "if", expression, block,
                [ "else", block ] ;

loop          = "while", expression,
                { loop_contract }, block ;

block         = "{", { statement }, "}" ;

expression    = disjunction ;
disjunction   = conjunction, { "||", conjunction } ;
conjunction   = equality, { "&&", equality } ;
equality      = comparison, { ("==" | "!="), comparison } ;
comparison    = sum, { ("<" | "<=" | ">" | ">="), sum } ;
sum           = product, { ("+" | "-"), product } ;
product       = unary, { ("*" | "/"), unary } ;

unary         = ("-" | "!"), unary
              | "move", identifier
              | "&", [ "mut" ], identifier
              | "@", identifier
              | primary ;

primary       = number
              | "true" | "false"
              | identifier
              | call
              | tensor_literal
              | "(", expression, ")" ;

call          = identifier, [ specialization ],
                "(", [ expression, { ",", expression } ], ")" ;

specialization = "::", "[",
                 type_argument, { ",", type_argument },
                 "]" ;

type_argument = type | natural ;

tensor_literal = "[",
                 expression, { ",", expression },
                 "]" ;

type          = "real" | "bool" | "unit"
              | "Tensor", "[", natural, { ",", natural }, "]"
              | "Event", "[", frame, "]"
              | "Tangent", "[", frame, "]"
              | "Covector", "[", frame, "]"
              | "Metric", "[", frame, "]"
              | "Connection", "[", frame, "]"
              | "Curvature", "[", frame, "]"
              | "QReg", "[", natural, "]"
              | "Bits", "[", natural, "]"
              | "Hybrid", "[", natural, ",", natural, "]"
              | "Cap", "[", resource, "]"
              | function_type ;

function_type = "fn", "(", [ type, { ",", type } ], ")",
                "->", type, [ effects ] ;

frame         = "Minkowski" | "Rindler" ;
resource      = "Compute" | "Quantum" | "IO" ;

identifier    = letter_or_underscore,
                { letter_or_underscore | digit } ;

natural       = digit, { digit } ;

number        = decimal_number, [ exponent ] ;
exponent      = ("e" | "E"), [ "+" | "-" ], digit, { digit } ;
```

Additional lexical and static rules:

- Identifiers in this revision use ASCII letters, digits, and underscores.
- The language name need not itself be a valid identifier.
- Integer-looking numeric expressions have type `real`; shape arguments are compile-time naturals.
- Nested tensor literals must be rectangular.
- Tensor dimensions and quantum-register sizes must be positive, except that the quantum component of `Hybrid[0,m]` may be empty.
- Variables are declared at function entry. Nested declarations and shadowing are disallowed.
- Functions have a single final return.
- Boolean operators are **strict**, not short-circuiting.
- Contract expressions are pure and cannot borrow mutable resources, measure qubits, or perform I/O.
- `result` is available in postconditions.
- `old(expression)` denotes the entry-state value in postconditions.
- Function references use `@name`; resource borrows use `&name` or `&mut name`.
- User-defined generic functions are not part of this revision. Generic intrinsics have compiler-known specialization rules.

These restrictions keep the language small enough to specify without pretending it is a general replacement for every existing systems language.

---

## 2.3 Type system

### Basic judgments

Typing uses a context of unrestricted values \(\Gamma\), affine resources \(\Delta\), and permitted effects \(\epsilon\):

\[
\Gamma;\Delta \vdash e:T\;!\epsilon.
\]

Typical rules include:

\[
\frac{\Gamma;\Delta\vdash a:\mathrm{real}
\qquad
\Gamma;\Delta\vdash b:\mathrm{real}}
{\Gamma;\Delta\vdash a+b:\mathrm{real}}.
\]

For equal-shaped tensors,

\[
\frac{\Gamma;\Delta\vdash A:\mathrm{Tensor}[S]
\qquad
\Gamma;\Delta\vdash B:\mathrm{Tensor}[S]}
{\Gamma;\Delta\vdash A+B:\mathrm{Tensor}[S]}.
\]

Tensor multiplication is elementwise. Contractions are explicit intrinsics. A scalar may multiply a tensor.

There is no implicit conversion between `bool` and `real`.

### Resource rules

The affine context tracks each resource as one of:

```text
available
immutably borrowed for the current call
mutably borrowed for the current call
moved
```

Rules:

- `move q` consumes `q`.
- A moved resource cannot be read until assigned a new value.
- `&mut q` requires unique access.
- Immutable and mutable borrows of the same resource cannot overlap.
- Call borrows cannot be returned, stored, or captured.
- Branches must agree on resource availability at their join.
- A loop backedge must restore its resource-state invariant.
- Dropping a quantum register means explicit or compiler-inserted backend disposal, not cloning or returning its amplitudes.

Capabilities are unforgeable host-issued handles. Borrowing a capability can authorize an operation without transferring ownership.

### Geometry rules

An event is not a vector. Allowed operations include:

\[
\operatorname{advance}_F:
\operatorname{Event}[F]\times\operatorname{Tangent}[F]
\to\operatorname{Event}[F],
\]

where this intrinsic denotes coordinate displacement within the supported chart—not a generally coordinate-invariant exponential map.

Metric contraction has signature

\[
\operatorname{inner}_F:
\operatorname{Metric}[F]\times
\operatorname{Tangent}[F]\times
\operatorname{Tangent}[F]\to\mathrm{real}.
\]

Coordinate conversion changes both the frame index and components using the appropriate Jacobian.

### Differentiation rules

For a differentiable pure function \(f:T\to\mathrm{real}\),

\[
\operatorname{grad}(f,x):T,
\]

where \(T\) is `real` or a fixed-shape real tensor.

For a differentiable pure function \(f:T\to U\),

\[
\operatorname{jvp}(f,x,v):U
\]

returns \(Df(x)v\), not a tuple containing the primal.

Only executed control-flow paths are differentiated. At nondifferentiable boundaries, the compiler either:

- rejects differentiation under a smoothness requirement; or
- uses an explicitly documented local derivative convention.

The language does not claim that differentiating a branch produces a derivative at the branch discontinuity.

### Quantum-classical types

- `QReg[n]`: an affine handle to \(n\) live qubits.
- `Bits[m]`: an ordinary classical bit vector.
- `Hybrid[n,m]`: an affine package containing \(n\) live qubits and \(m\) measured classical bits.

For example:

\[
\operatorname{measure\_first}:
QReg[2]\times \operatorname{view}Cap[Quantum]
\to Hybrid[1,1].
\]

The measured qubit is removed from the live quantum component. The residual quantum state is conditioned on the returned outcome.

---

## 2.4 Intrinsic interface

The following intrinsics define the facilities used by the examples. Tensor overloads act elementwise unless stated otherwise.

| Intrinsic | Meaning |
|---|---|
| `exp`, `log`, `sqrt`, `sin`, `cos`, `abs` | Scalar numerical operations |
| `sum(Tensor[S]) -> real` | Reduction |
| `grad(@f, x)` | Reverse-mode scalar-output gradient |
| `jvp(@f, x, v)` | Forward-mode directional derivative |
| `parmap(cap, @f, tensor)` | Capability-authorized parallel elementwise application |
| `event_M(Tensor[4])` | Construct a Minkowski event |
| `tangent_M(Tensor[4])` | Construct a Minkowski tangent |
| `metric_M(Tensor[4,4])` | Construct a Minkowski-coordinate metric |
| `advance_M(event, tangent)` | Add a coordinate displacement |
| `inner_M(metric, u, v)` | Metric contraction |
| `levi_civita_M(@metric_field, event)` | Christoffel coefficients from metric derivatives |
| `connection_apply_M(connection, u, v)` | \(\Gamma^\mu_{\alpha\beta}u^\alpha v^\beta\) |
| `transform_MR`, `transform_RM` | Rindler/Minkowski chart transformations in their domains |
| `riemann_M(@metric_field, event)` | Riemann curvature from the Levi-Civita connection |
| `qalloc::[n](cap)` | Allocate \(\lvert0\rangle^{\otimes n}\) |
| `ry(&mut q, i, angle)` | Apply \(R_y(\mathrm{angle})\) |
| `cx(&mut q, control, target)` | Controlled-X |
| `measure_first(move q, cap)` | Measure qubit zero and return the hybrid remainder |
| `dispose(move hybrid, cap)` | Dispose remaining qubits; return stored bits |
| `bit_at(bits, i) -> real` | Return \(0\) or \(1\), with checked index |
| `write_real(cap, value) -> unit` | Authorized output |

General geometry intrinsic families have the corresponding signatures for either supported frame.

Tensor shape, index range, metric nonsingularity, and chart-domain conditions are proof obligations or checked preconditions.

---

## 2.5 High-level operational semantics

A machine configuration contains:

\[
\langle e,\rho,H,Q,C,\mathcal D\rangle,
\]

where:

- \(\rho\) maps local variables to values;
- \(H\) contains owned classical buffers;
- \(Q\) contains quantum backend handles;
- \(C\) records available capabilities;
- \(\mathcal D\) is the dependency graph of scheduled operations.

### Pure computation

A pure expression denotes a value independently of execution placement. Its data dependencies constrain scheduling; independent nodes may run simultaneously.

Floating-point reduction order is part of the execution policy:

- deterministic mode uses a specified reduction tree;
- relaxed mode permits reassociation and explicitly weaker reproducibility.

### Mutation

Local mutation denotes replacement of a variable’s current value. The compiler lowers this into SSA values and merge nodes.

Buffer reuse is an optimization justified by ownership and liveness, not observable aliasing.

### Differentiation

Forward mode propagates pairs conceptually equivalent to

\[
(v,\dot v).
\]

Reverse mode evaluates the primal dependency graph and traverses its differentiable operations backward, accumulating cotangents.

The implementation may erase this conceptual representation into optimized generated code. Reverse-mode storage costs do not disappear merely because the feature is native.

### Quantum execution

Unitary operations mutate a uniquely borrowed quantum resource. Measurement produces a probabilistic transition governed by the Born rule.

A hypothetical accelerator is accessed through the same abstract interface as a simulator or physical device. Its existence and speed are not assumed by the semantics.

### Failure

Execution may:

- return a value;
- diverge;
- produce an explicit checked failure, such as a domain, contract, resource, or fuel error.

Memory corruption and unauthorized resource access are not allowed semantic outcomes.

---

## 2.6 Zero-cost abstractions: precise claim

“Zero-cost” means that static types, frame tags, proven contracts, and ownership metadata need not occupy runtime space after compilation.

It does **not** mean:

- reverse-mode autodiff needs no tape;
- a tensor contraction costs nothing;
- quantum measurement has no latency;
- unproved contracts require no checks;
- bounds checks always disappear;
- GPU transfers are free.

Safety checks may be erased only when their obligations are discharged.

---

# 3. Four Nontrivial Aether-Ω Programs

The first four programs use the full language design. The physics source in §5 uses the implemented scalar subset.

## 3.1 Inverse estimation with forward and reverse autodiff

This program estimates a positive parameter from an exponential attenuation observation.

```text
fn attenuation_loss(a: real) -> real {
    var predicted: real = exp(-0.75 * a);
    var residual: real = predicted - 0.4;
    return residual * residual;
}

fn fit_acceleration(initial: real) -> real
requires(initial > 0)
ensures(result > 0)
{
    var a: real = initial;
    var g: real = 0;
    var forward_check: real = 0;
    var proposal: real = 0;
    var i: real = 0;

    while i < 200
    invariant(a > 0)
    invariant(i >= 0)
    {
        g = grad(@attenuation_loss, a);
        forward_check = jvp(@attenuation_loss, a, 1);

        proposal = a - 0.1 * (g + forward_check) / 2;

        if proposal > 0 {
            a = proposal;
        } else {
            a = a / 2;
        }

        i = i + 1;
    }

    return a;
}
```

The two derivative modes compute the same mathematical derivative here. Their average is used only to exercise both modes; a production optimizer would not normally calculate both every iteration.

---

## 3.2 Geometry-typed inertial geodesic integration

```text
fn flat_metric(p: Event[Minkowski]) -> Metric[Minkowski] {
    return metric_M([
        [-1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ]);
}

fn inertial_geodesic(
    initial: Event[Minkowski],
    velocity: Tangent[Minkowski],
    step: real
) -> Event[Minkowski]
requires(step > 0)
requires(inner_M(flat_metric(initial), velocity, velocity) == -1)
{
    var p: Event[Minkowski] = initial;
    var u: Tangent[Minkowski] = velocity;
    var gamma: Connection[Minkowski] =
        levi_civita_M(@flat_metric, initial);
    var acceleration: Tangent[Minkowski] =
        tangent_M([0, 0, 0, 0]);
    var i: real = 0;

    while i < 1024
    invariant(i >= 0)
    {
        gamma = levi_civita_M(@flat_metric, p);
        acceleration = -connection_apply_M(gamma, u, u);
        u = u + step * acceleration;
        p = advance_M(p, step * u);
        i = i + 1;
    }

    return p;
}
```

For this constant Minkowski metric, \(\Gamma^\mu_{\alpha\beta}=0\), so the algorithm gives the exact affine geodesic in real arithmetic. This is not a claim that the same update is an exact curved-spacetime integrator.

---

## 3.3 Parallel differentiable tensor optimization

```text
fn lane_loss(x: real) -> real {
    var residual: real = sin(x) - 0.25;
    return residual * residual + 0.001 * x * x;
}

fn lane_gradient(x: real) -> real {
    return grad(@lane_loss, x);
}

fn optimize_tensor(
    executor: view Cap[Compute],
    initial: Tensor[4096]
) -> Tensor[4096] !{compute}
{
    var x: Tensor[4096] = initial;
    var g: Tensor[4096] = initial * 0;
    var i: real = 0;

    while i < 100 {
        g = parmap(executor, @lane_gradient, x);
        x = x - 0.05 * g;
        i = i + 1;
    }

    return x;
}
```

The 4096 lane evaluations are independent. CPU/GPU partitioning and batching are scheduler decisions. No quantum speedup is implied for this classical workload.

---

## 3.4 Quantum-classical parameter-shift estimation

```text
fn quantum_shot(
    device: view Cap[Quantum],
    theta: real
) -> Hybrid[1,1] !{quantum}
{
    var q: QReg[2] = qalloc::[2](device);

    ry(&mut q, 0, theta);
    cx(&mut q, 0, 1);

    return measure_first(move q, device);
}

fn estimate_z(
    device: view Cap[Quantum],
    theta: real
) -> real !{quantum}
{
    var sample: Hybrid[1,1] = quantum_shot(device, theta);
    var bits: Bits[1] = dispose(move sample, device);
    var total: real = 1 - 2 * bit_at(bits, 0);
    var i: real = 1;

    while i < 4096 {
        sample = quantum_shot(device, theta);
        bits = dispose(move sample, device);
        total = total + 1 - 2 * bit_at(bits, 0);
        i = i + 1;
    }

    return total / 4096;
}

fn parameter_shift(
    device: view Cap[Quantum],
    theta: real
) -> real !{quantum}
{
    var plus: real =
        estimate_z(device, theta + 1.5707963267948966);
    var minus: real =
        estimate_z(device, theta - 1.5707963267948966);

    return (plus - minus) / 2;
}
```

The circuit prepares

\[
\cos(\theta/2)\lvert00\rangle+
\sin(\theta/2)\lvert11\rangle.
\]

Thus

\[
\langle Z_0\rangle=\cos\theta,
\qquad
\frac{d}{d\theta}\langle Z_0\rangle=-\sin\theta.
\]

The parameter-shift identity is exact for the expectation. The finite-shot estimator is noisy. The program never differentiates a sampled bit as if it were a smooth real value.

---

# 4. Mathematical Formulation

## 4.1 Minkowski spacetime

Use units \(c=1\) and coordinates

\[
x^\mu=(t,x,y,z).
\]

The metric is

\[
g_{\mu\nu}=\operatorname{diag}(-1,1,1,1),
\]

so

\[
ds^2=-dt^2+dx^2+dy^2+dz^2.
\]

Both ships move along \(x\), with \(y=z=0\). The spacetime remains four-dimensional; the experiment occupies a two-dimensional invariant subspace.

---

## 4.2 Rindler coordinates

In the right Rindler wedge \(x>|t|\), define

\[
t=\rho\sinh\eta,
\qquad
x=\rho\cosh\eta,
\qquad
\rho>0.
\]

Then

\[
ds^2=-\rho^2d\eta^2+d\rho^2+dy^2+dz^2.
\]

For an observer at fixed \(\rho\),

\[
d\tau=\rho\,d\eta,
\qquad
a=\frac1\rho.
\]

Choose

\[
\rho_A=1,\qquad \rho_B=2.
\]

Consequently,

\[
a_A=1,\qquad a_B=\frac12.
\]

These are different proper accelerations. Their trajectories share the same Rindler horizon, and their Rindler spatial separation is constant.

This choice matters: arbitrary uniformly accelerated trajectories need not form a Born-rigid pair and need not maintain bidirectional communication indefinitely.

With a physical length scale \(L\), the corresponding proper accelerations are \(c^2/L\) and \(c^2/(2L)\), and coordinate times are scaled by \(L/c\).

---

## 4.3 Null propagation

For radial light,

\[
0=-\rho^2d\eta^2+d\rho^2,
\]

hence

\[
\frac{d\rho}{d\eta}=s\rho,
\qquad s\in\{+1,-1\}.
\]

Here \(s=+1\) denotes \(A\to B\), and \(s=-1\) denotes \(B\to A\).

The exact solution is

\[
\rho(\eta)=\rho_e e^{s(\eta-\eta_e)}.
\]

In both directions,

\[
\Delta\eta=\ln 2.
\]

Each finite emission time has a finite reception time. Continuous communication is therefore possible for these idealized observers.

---

## 4.4 Proper-time mapping and redshift

At fixed emitter and receiver radii,

\[
\tau_e=\rho_e\eta_e,
\qquad
\tau_r=\rho_r(\eta_e+\ln2).
\]

Differentiating,

\[
\frac{d\tau_r}{d\tau_e}=\frac{\rho_r}{\rho_e}.
\]

Conservation of successive wave crests gives

\[
\boxed{
\frac{\nu_r}{\nu_e}
=
\frac{d\tau_e}{d\tau_r}
=
\frac{\rho_e}{\rho_r}
}.
\]

Therefore,

\[
\boxed{\nu_{A\to B}/\nu_A=1/2},
\qquad
\boxed{\nu_{B\to A}/\nu_B=2}.
\]

The ratios are constant even though both inertial velocities vary.

---

## 4.5 Exact inertial Doppler formula

The observer four-velocity is

\[
u^\mu=(\cosh\eta,\sinh\eta,0,0).
\]

For a photon propagating in direction \(s\),

\[
k^\mu=\omega(1,s,0,0).
\]

The measured frequency is proportional to

\[
-u_\mu k^\mu
=
\omega(\cosh\eta-s\sinh\eta)
=
\omega e^{-s\eta}.
\]

Since inertial photon energy is constant along the flat-spacetime null ray,

\[
\boxed{
\frac{\nu_r}{\nu_e}
=
e^{-s(\eta_r-\eta_e)}
}.
\]

Using \(\eta_r-\eta_e=\ln2\) reproduces \(1/2\) and \(2\).

There is no additional multiplicative gravitational correction. The Rindler lapse ratio and this Doppler ratio describe the same observable.

---

## 4.6 Light travel time

A one-way travel time between different observers requires a clock convention. Here the reported travel time is the difference in **Minkowski coordinate time**:

\[
\Delta t
=
\rho_r\sinh(\eta_e+\ln2)
-\rho_e\sinh\eta_e.
\]

Using

\[
\sinh(\ln2)=\frac34,
\qquad
\cosh(\ln2)=\frac54,
\]

gives

\[
\boxed{
\Delta t_{A\to B}
=
\frac32 e^{\eta_e}
},
\]

and

\[
\boxed{
\Delta t_{B\to A}
=
\frac34 e^{-\eta_e}
}.
\]

These are positive for every finite emission rapidity.

A difference such as \(\tau_r-\tau_e\) would subtract readings of different clocks and is not a convention-independent one-way elapsed proper time.

---

# 5. Executable Compiler, Interpreter, and Simulation

## 5.1 Implemented subset

The prototype implements:

- `real` and `bool`;
- typed function definitions and calls;
- initialized function-local variables;
- assignment;
- strict Boolean operators;
- arithmetic and comparisons;
- nested `if`/`else`;
- `while`;
- final `return`;
- `exp`, `log`, `sqrt`, and `abs`;
- type checking;
- recursion rejection;
- SSA construction with real \(\phi\)-nodes;
- LLVM-like textual rendering;
- execution of the generated SSA objects;
- a global execution-fuel limit.

It intentionally rejects unsupported full-language syntax.

The text backend is **LLVM-like**, not valid LLVM assembly. The interpreter executes the SSA representation that the text backend renders; it does not interpret the source AST.

## 5.2 Complete runnable artifact

```python
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
```

---

# 6. Implementation Details

## 6.1 SSA construction

The compiler uses structured control flow to construct SSA directly.

### Assignments

An assignment changes the source-variable-to-register map:

```text
x = x + 1;
```

becomes conceptually:

```text
%v.7 = const double 1.0
%v.8 = fadd double %v.3, %v.7
```

Subsequent references to `x` use `%v.8`.

### Branches

A branch join receives a \(\phi\)-node when the two branches produce different versions:

```text
%v.12 = phi double [ %v.8, %b1 ], [ %v.11, %b2 ]
```

### Loops

The loop header receives a \(\phi\)-node for every in-scope variable:

\[
x_h=\phi(x_{\mathrm{entry}},x_{\mathrm{backedge}}).
\]

This is intentionally conservative. An optimization pass could remove redundant loop phis.

### Simultaneous phi evaluation

The interpreter first reads every selected incoming value and only then writes phi destinations. This matters for loop-carried permutations such as swapping two variables.

Updating phis sequentially would be incorrect.

---

## 6.2 Numerical time stepping

The null ODE is

\[
\rho'=s\rho.
\]

For step size \(h=8/N\), RK4 gives

\[
\rho_{j+1}=R(sh)\rho_j,
\]

where

\[
R(z)=1+z+\frac{z^2}{2}+\frac{z^3}{6}+\frac{z^4}{24}.
\]

The first detector crossing is bracketed by \(\rho_j\) and \(\rho_{j+1}\). Within that step, the code uses logarithmic interpolation:

\[
\theta
=
\frac{\ln(\rho_{\mathrm{target}}/\rho_j)}
     {\ln(\rho_{j+1}/\rho_j)},
\qquad
0\le\theta\le1.
\]

Thus

\[
\Delta\eta_N=(j+\theta)h.
\]

This interpolation is exact for the step’s fitted exponential. It does not replace the RK4 multiplier by the exact \(e^{sh}\); therefore the numerical result still has RK4 discretization error.

The auxiliary characteristic continues for all \(N\) steps. Physically, reception occurs at the first crossing and the displayed photon terminates there. The continued integration is merely an auxiliary numerical trajectory.

---

## 6.3 Why this has a meaningful convergence test

In exact arithmetic, the numerical delays are

\[
d_N^+
=
\frac{h\ln2}{\ln R(h)},
\]

and

\[
d_N^-
=
-\frac{h\ln2}{\ln R(-h)}.
\]

Since

\[
\ln R(z)=z-\frac{z^5}{120}+O(z^6),
\]

we obtain

\[
d_N^+
=
\ln2+\frac{\ln2}{120}h^4+O(h^5),
\]

and

\[
d_N^-
=
\ln2+\frac{\ln2}{120}h^4+O(h^5).
\]

Both leading errors are positive. The fifth-order terms differ by direction.

Consequently,

\[
\frac{|d_N-\ln2|}
     {|d_{2N}-\ln2|}
\longrightarrow16.
\]

This is a discretization convergence test, not merely a comparison of identical exact formulas at different sample counts.

---

## 6.4 Numerical versus analytic responsibilities

The separation is deliberate:

| Quantity | Computation |
|---|---|
| Observer trajectories | Exact Rindler coordinate formulas executed in SSA |
| Signal flight rapidity | Numerical RK4 integration executed in SSA |
| Reception proper time | Numerical flight rapidity inserted into exact clock map |
| Frequency ratio | Doppler formula evaluated with numerical flight rapidity |
| Coordinate travel time | Numerical reception event minus emission event |
| Null residual | Computed from numerical endpoint events |
| Reference answers | Independent closed-form identities in Python |
| ASCII photon drawing | Exact characteristic, for clean visualization |
| Continuous communication sampling | 513 emissions over 512 intervals |

The simulation is not a numerical solution of Einstein’s field equations. The metric and observer worldlines are prescribed exactly.

---

# 7. Results and Numerical Validation

## 7.1 Analytic reference table

The following values are exact-formula references, rounded for display. They are not represented as captured interpreter output.

\[
d=\ln2=0.6931471805599453\ldots
\]

| Emission \(\eta_e\) | \(\tau_{e,A}\) | \(\tau_{r,B}\) | \(\Delta t_{A\to B}\) | \(\tau_{e,B}\) | \(\tau_{r,A}\) | \(\Delta t_{B\to A}\) |
|---:|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.0 | 1.386294361 | 1.500000000 | 0.0 | 0.693147181 | 0.750000000 |
| 0.5 | 0.5 | 2.386294361 | 2.473081906 | 1.0 | 1.193147181 | 0.454897995 |
| 1.0 | 1.0 | 3.386294361 | 4.077422743 | 2.0 | 1.693147181 | 0.275909581 |
| 1.5 | 1.5 | 4.386294361 | 6.722533606 | 3.0 | 2.193147181 | 0.167347620 |
| 2.0 | 2.0 | 5.386294361 | 11.083584148 | 4.0 | 2.693147181 | 0.101501462 |

The exact frequency ratios are:

| Direction | Receiver/emitter frequency |
|---|---:|
| \(A\to B\) | \(0.5\) |
| \(B\to A\) | \(2.0\) |

---

## 7.2 Expected discretization scale

The leading error estimate is

\[
E_N\sim \frac{\ln2}{120}\left(\frac8N\right)^4.
\]

| Steps \(N\) | Step size \(h\) | Leading-order delay-error estimate |
|---:|---:|---:|
| 512 | \(1/64\) | \(3.44\times10^{-10}\) |
| 1024 | \(1/128\) | \(2.15\times10^{-11}\) |
| 2048 | \(1/256\) | \(1.34\times10^{-12}\) |

These are asymptotic estimates, not measured floating-point errors. The executable prints actual errors and refinement ratios separately for both directions.

At sufficiently fine resolution, rounding error will prevent continued fourth-order convergence.

---

## 7.3 Physical consistency checks

For each numerical emission/reception pair, the code evaluates

\[
r_{\mathrm{null}}
=
\frac{
\left|
(x_r-x_e)-s(t_r-t_e)
\right|
}{
1+|t_e|+|x_e|+|t_r|+|x_r|
}.
\]

The normalization measures endpoint null consistency relative to the coordinate scale. It is not a relative error in a potentially very small one-way travel time.

The program also independently checks:

- positive finite reception delay;
- agreement with exact frequency ratios;
- agreement with exact Minkowski travel times;
- refinement ratios compatible with fourth-order convergence;
- correct loop-phi semantics;
- rejection of several invalid source programs.

---

## 7.4 Frequency versus emitter proper time

For stationary Rindler observers, the ratio is independent of emission time. Flat plots are the physically correct result.

```text
A -> B

nu_r / nu_e
0.5 |*****************************************
    +-----------------------------------------> tau_A
     0                                        2
```

```text
B -> A

nu_r / nu_e
2.0 |*****************************************
    +-----------------------------------------> tau_B
     0                                        4
```

A changing inertial velocity does not require a changing frequency ratio: the emission and reception rapidities differ by a constant.

---

## 7.5 Text-based 3D spacetime diagram

The physical experiment has \(y=z=0\). A three-coordinate viewport can display \((x,y,t)\); the unused fourth coordinate is explicitly suppressed.

```text
                         t
                         ^
                         |
                         |                 B worldline
                         |              .´
                         |           .´
                         |        .´   /  outward null ray
                         |     .´    /
                         |   A     /
                         | .´ \  /
                         |     \/   inward null ray
                         +----------------------------> x
                        /
                       y

                    z = 0; all worldlines also have y = 0
```

This diagram is schematic. The executable produces a fixed-scale orthographic Minkowski viewport with actual event coordinates.

---

# 8. Ten Sequential ASCII Frames

## 8.1 Coordinate convention

The compact frames below use a co-moving three-coordinate viewport

\[
(\rho,y,\eta).
\]

The camera tracks the current \(\eta\)-slice. All displayed events have \(y=0\), and \(z\) is suppressed.

Each horizontal strip spans \(1\le\rho\le2\) with 20 equal intervals.

- `A`, `B`: ships.
- `>`: newest highlighted outward pulse.
- `<`: newest highlighted inward pulse.
- At emission, pulse symbols overlap the ship labels.
- Highlighted pulse pairs are emitted at \(\eta=0,0.8,1.6\).
- These highlights sample the continuous laser streams; the executable’s Minkowski view also displays pairs emitted every \(0.2\).

The current highlighted pulse positions are

\[
\rho_+=e^{\eta-\eta_{\mathrm{launch}}},
\qquad
\rho_-=2e^{-(\eta-\eta_{\mathrm{launch}})}.
\]

These frames therefore show actual characteristic motion in Rindler coordinates, not an invented frequency oscillation.

```text
FRAME 00 — eta = 0.0
eta ^
    |  A-------------------B
    +-/----------------------> rho
     y
```

```text
FRAME 01 — eta = 0.2
eta ^
    |  A--->--------<------B
    +-/----------------------> rho
     y
```

```text
FRAME 02 — eta = 0.4
eta ^
    |  A------<-->---------B
    +-/----------------------> rho
     y
```

```text
FRAME 03 — eta = 0.6
eta ^
    |  A-<------------->---B
    +-/----------------------> rho
     y
```

```text
FRAME 04 — eta = 0.8
eta ^
    |  A-------------------B
    +-/----------------------> rho
     y
```

```text
FRAME 05 — eta = 1.0
eta ^
    |  A--->--------<------B
    +-/----------------------> rho
     y
```

```text
FRAME 06 — eta = 1.2
eta ^
    |  A------<-->---------B
    +-/----------------------> rho
     y
```

```text
FRAME 07 — eta = 1.4
eta ^
    |  A-<------------->---B
    +-/----------------------> rho
     y
```

```text
FRAME 08 — eta = 1.6
eta ^
    |  A-------------------B
    +-/----------------------> rho
     y
```

```text
FRAME 09 — eta = 1.8
eta ^
    |  A--->--------<------B
    +-/----------------------> rho
     y
```

The apparent reversal in the order of the two photon symbols is correct: the counter-propagating photons cross.

A static Markdown document cannot refresh a terminal in real time. The `--animate` option performs terminal refreshes with a nominal 120 ms pause between frames. This is interactive animation, not a hard-real-time guarantee.

---

# 9. Formal Correctness Argument

## 9.1 Scalar type preservation

For the implemented subset, define a well-typed environment as one whose values agree with their declared `real` or `bool` types.

The checker establishes:

1. Every variable is initialized before use.
2. Every assignment preserves the variable’s type.
3. Arithmetic operands are real.
4. Boolean operands are Boolean.
5. Conditions are Boolean.
6. Function argument and return types agree.
7. Every source call resolves.
8. The call graph is acyclic.

For an expression \(e:T\), evaluation either produces a value of \(T\), encounters a defined numerical/runtime failure, or fails to terminate through called control flow.

The statement preservation argument proceeds by structural induction:

- Assignment replaces a value with one of the same type.
- Both branches preserve the same environment typing.
- A loop body preserves the types required by its next condition evaluation.

This is a type-safety argument, not a termination proof.

---

## 9.2 SSA lowering correctness

Associate each source variable with its current SSA register.

### Straight-line code

Expression lowering preserves operand dependencies. Assignment updates only the association, matching source replacement semantics.

### Conditional code

Each branch is lowered from the same incoming association. At the join, the selected phi operand equals the value from the executed predecessor.

### Loop code

Header phis choose:

- the pre-loop value on the first entry;
- the body’s final value on subsequent entries.

The loop condition therefore sees exactly the values that source semantics would see at the corresponding iteration.

Simultaneous phi evaluation preserves loop-carried dependencies, including swaps.

By induction on executed blocks, the SSA interpreter and the source operational semantics agree for successful scalar executions, subject to using the same primitive arithmetic.

This argument assumes the compiler implementation matches the described construction. It is not a machine-checked proof of the Python source.

---

## 9.3 Full-language resource safety

The intended full-language proof would add:

- affine-context preservation;
- exclusive-borrow preservation;
- capability non-forgeability;
- absence of escaping call borrows;
- typed quantum-state transition preservation.

The key no-cloning property follows structurally from the absence of a copying operation for `QReg` and `Hybrid` values.

However, enforcing the source rule does not prove a hardware provider faithfully implements the advertised operation. The device driver and capability boundary remain part of the trusted computing base.

---

## 9.4 Geometric consistency

For a Rindler observer,

\[
u^\mu=(\cosh\eta,\sinh\eta,0,0).
\]

Therefore,

\[
u^\mu u_\mu=-\cosh^2\eta+\sinh^2\eta=-1.
\]

Since \(d\eta/d\tau=1/\rho\),

\[
a^\mu
=
\frac1\rho(\sinh\eta,\cosh\eta,0,0),
\]

so

\[
a^\mu a_\mu=\frac1{\rho^2}.
\]

Thus the claimed proper acceleration is correct.

For a photon characteristic \(\rho'=s\rho\),

\[
\frac{dt}{d\eta}
=
\rho(s\sinh\eta+\cosh\eta),
\]

\[
\frac{dx}{d\eta}
=
\rho(s\cosh\eta+\sinh\eta).
\]

For \(s=\pm1\),

\[
\frac{dx}{dt}=s.
\]

Hence the exact characteristic is a Minkowski null line.

---

## 9.5 Frequency consistency

The frequency ratio follows independently from:

1. proper-time separation of successive crests; and
2. the invariant measured energy \(-u\cdot k\).

Both yield

\[
\nu_r/\nu_e=\rho_e/\rho_r.
\]

This agreement rules out the common mistake of applying a Doppler factor and then an additional Rindler gravitational factor to the same ray.

---

## 9.6 Numerical consistency

RK4 is fourth-order consistent for the smooth linear null ODE. The detector crossing is transversal because

\[
\frac{d\rho}{d\eta}=s\rho\ne0
\]

at either detector.

The logarithmic event interpolation produces the explicit modified-delay formula in §6.3, which establishes fourth-order convergence in exact arithmetic.

Floating-point roundoff is a separate error source and eventually dominates.

---

# 10. Limitations and Future Work

## 10.1 Language implementation coverage

The runnable compiler is not an implementation of the entire language specification.

Missing executable full-language components include:

- tensor storage and shape checking;
- forward and reverse autodiff;
- geometry-aware types and intrinsic expansion;
- capability objects and effect checking;
- affine quantum resources;
- formal-contract parsing and verification;
- CPU/GPU heterogeneous scheduling;
- a quantum simulator or hardware adapter.

These are specified interfaces and semantics, not completed backend modules.

A credible implementation roadmap would begin with typed tensor IR, ownership analysis, and effect checking before attempting accelerator scheduling.

---

## 10.2 Physics coverage

The model assumes:

- flat spacetime;
- prescribed eternally accelerated trajectories;
- ideal point observers;
- ideal monochromatic lasers;
- no recoil or radiation reaction;
- no finite-aperture loss;
- no acceleration noise;
- no detector bandwidth limit;
- no backreaction;
- no transverse motion.

“Gravitational redshift” here refers to the accelerated-frame lapse effect. The Riemann tensor is zero.

A genuinely curved-spacetime extension would require a nonconstant metric, geodesic integration, parallel transport or equivalent wave-vector evolution, and more general event detection.

---

## 10.3 Visualization coverage

The ASCII viewport is a projection of spacetime events, not a simulation of what either astronaut visually sees.

Frames use common Rindler time. Ship labels in the same frame generally have different Minkowski coordinate times.

A realistic optical rendering would require past-light-cone intersection, aberration, intensity transport, and possibly finite exposure integration.

---

## 10.4 Verification coverage

The argument is mathematical and implementation-oriented, but not machine checked.

Production verification would require:

- a formal source semantics;
- a formal SSA semantics;
- a proved or translation-validated lowering;
- an explicit floating-point model;
- verified library contracts;
- sound treatment of accelerator and quantum effects;
- proof-carrying assumptions at the host boundary.

---
## Reproducibility, Numerical Interpretation, and Deployment

### Implementation boundary

The executable artifact implements a scalar subset of the proposed
language. Tensor operations, automatic differentiation, geometry-aware
typing, formal contracts, capability checking, heterogeneous scheduling,
and quantum resources are not implemented by the Python compiler.

The Streamlit frontend adds third-party presentation dependencies.
The scalar compiler and interpreter themselves use only the Python
standard library.

### Meaning of the step counts

The propagation routine integrates an auxiliary characteristic over

$$
0 \le \eta-\eta_e \le 8
$$

using

$$
h=\frac{8}{N}.
$$

Physical reception occurs near

$$
\eta-\eta_e=\ln 2.
$$

The number of integration intervals before reception is therefore
approximately

$$
N_{\mathrm{flight}}
\approx
\frac{N\ln 2}{8}.
$$

At $N=512$, this is approximately 44.36 intervals, with the crossing
contained in the next interval.

Thus, “512 propagation steps” must not be interpreted as 512 steps
between emission and reception. The remaining integration steps extend
an auxiliary characteristic beyond detection.

Separately, the communication sweep uses 512 emission intervals,
corresponding to 513 emission samples per direction.

### Numerical event interpolation

For the linear characteristic equation

$$
\rho'=s\rho,
$$

RK4 advances the state by

$$
\rho_{j+1}=R(sh)\rho_j,
$$

where

$$
R(z)=1+z+\frac{z^2}{2}+\frac{z^3}{6}+\frac{z^4}{24}.
$$

The event locator interpolates logarithmically between adjacent states.
In exact arithmetic, the corresponding delays are

$$
d_N^+=\frac{h\ln 2}{\ln R(h)}
$$

and

$$
d_N^-=-\frac{h\ln 2}{\ln R(-h)}.
$$

This yields fourth-order event-time convergence. The method exploits
the exponential structure of this particular ODE and is not a
general-purpose event-location prescription for curved-spacetime
geodesics.

### Two frequency estimators at finite resolution

The exact continuum theory gives identical frequency ratios from
crest timing and the invariant photon-energy formula.

The current numerical implementation evaluates the Doppler estimator

$$
q_{\mathrm{Doppler},N}=\exp(-s d_N).
$$

Because $d_N$ has discretization error, this estimator differs slightly
from the exact ratio.

By contrast, the numerical reception-time mapping used by this
stationary benchmark is

$$
\tau_r=\rho_r(\eta_e+d_N).
$$

Since $d_N$ is independent of $\eta_e$, differentiation gives

$$
q_{\mathrm{crest},N}
=
\frac{d\tau_e}{d\tau_r}
=
\frac{\rho_e}{\rho_r}.
$$

Therefore the two estimators need not agree exactly at finite
resolution. Their discrepancy is a useful consistency diagnostic,
not a new physical frequency effect.

For the current method, the discrepancy is fourth order in the
step size in exact arithmetic.

### Visualization provenance

Observer coordinates and displayed photon characteristics are
evaluated from analytic formulas. The ASCII viewport illustrates the
reference physical solution rather than displaying the accumulated
RK4 trajectory error.

Frames use common Rindler time. They are not simultaneous
Minkowski-time snapshots and do not represent the optical appearance
seen by an astronaut.

### Execution evidence

Analytic tables in this paper are reference calculations, not
execution transcripts.

A reproducible numerical report should identify:

- the repository commit;
- the Python version;
- installed dependency versions;
- the workflow run;
- the captured validation log;
- the generated IR;
- the numerical CSV when using the web interface.

A successful automated run establishes that the included checks
passed in that environment. It does not establish complete compiler
correctness or a machine-checked physical proof.

### Deployment and security

The public web interface executes only the bundled program.

It does not accept arbitrary visitor-supplied Aether-Ω source, Python
code, filesystem paths, or shell commands.

This restriction reduces exposure but is not a formal security
guarantee. The hosting platform, Python runtime, dependencies, and
application code remain part of the trusted computing base.

Streamlit caching may reuse previously computed successful results.
A displayed result is not necessarily a new execution for each visitor.

# 11. Conclusion

Aether-Ω can be coherently designed around pure mathematical computation, affine resources, capability-authorized effects, geometry-aware values, and native differentiation.

The supplied prototype demonstrates a real executable compiler path rather than a source-to-Python substitution: parsing and type checking lead to SSA with branch and loop phis, which is both rendered as LLVM-like text and executed by an interpreter.

For the selected Rindler observers:

\[
a_A=1,\qquad a_B=\frac12,
\]

\[
\Delta\eta=\ln2,
\]

\[
\frac{\nu_{A\to B}}{\nu_A}=\frac12,
\qquad
\frac{\nu_{B\to A}}{\nu_B}=2,
\]

\[
\Delta t_{A\to B}=\frac32e^{\eta_e},
\qquad
\Delta t_{B\to A}=\frac34e^{-\eta_e}.
\]

The numerical method has an analytically established fourth-order event-time error and a runnable multi-resolution validation procedure.

The boundary between completed executable functionality and proposed language facilities is explicit.

---

# 12. Brutal Self-Critique and Adversarial Analysis

## 12.1 What is approximate, incomplete as an implementation, or easy to misread

### The full language is a design, not a working heterogeneous compiler

The Python artifact implements a scalar subset. It does not provide working GPU execution, autodiff, geometry types, contracts, or quantum resources.

Calling it a complete implementation of every Aether-Ω feature would be false.

### No execution occurred inside this conversation

The response supplies executable code and analytically derived references. It does not supply independently observed runtime logs.

That fails the literal request to execute the artifact here. Inventing a transcript would conceal rather than fix that limitation.

### The problem is deliberately specialized

The two ships share a Rindler horizon. This yields constant frequency ratios and identical Rindler flight intervals in both directions.

This is a legitimate nontrivial configuration with different proper accelerations, but it is much easier than arbitrary accelerated worldlines.

### The numerical method exploits the ODE structure

Logarithmic event interpolation is particularly appropriate for exponential characteristics. It should not be transplanted unchanged into a general geodesic solver.

### “Full numerical simulation” has a bounded meaning here

The signal characteristic and emission sampling are time-stepped. The metric and worldlines are analytic inputs.

The program does not numerically evolve the ships’ propulsion, solve Maxwell’s equations, or integrate Einstein’s equations.

### The visualization uses exact characteristics

This makes the drawings clean and physically interpretable, but means the animation is not a magnified display of numerical integration error.

### The zero-cost claim is conditional

Static metadata can disappear. Actual work, transfer costs, tapes, unresolved checks, and resource management cannot.

---

## 12.2 Performance bottlenecks

The interpreter is intentionally slow relative to native scientific code:

- Every instruction is a Python object operation.
- Registers live in dictionaries.
- Blocks use string labels.
- Phi selection performs linear searches over incoming edges.
- Function calls recursively enter the Python interpreter.
- Redundant phis are generated for unchanged variables.
- No constant folding, dead-code elimination, inlining, or loop optimization occurs.
- No tensor vectorization exists.
- The source recalculates exponentials in several observables.
- Terminal output can dominate visualization time.

A production compiler would use compact typed IR, optimization passes, native code generation, and batched numerical kernels.

The physics problem itself does not need a compiler or numerical solver to obtain its exact answers; the solver exists to exercise and validate the compilation pipeline.

---

## 12.3 Where formal guarantees break

### Compiler correctness is argued, not proved

A bug in parsing, lowering, or interpretation could invalidate the correspondence argument.

### Python is trusted

The runtime, `math` library, floating-point implementation, and host environment are outside the proof.

### Fuel is not a source-language termination proof

Fuel bounds interpreter work by failure. It does not prove a source loop terminates normally.

### Resource security is not implemented in the prototype

The host writes the IR file and terminal output directly. Those operations are not mediated by the proposed Aether-Ω capability system.

### Full-language contracts need a semantics choice

Mathematical-real contracts and floating-point execution are not automatically interchangeable. A production implementation must specify which assertions concern exact models, actual machine values, or error bounds relating the two.

### Quantum safety does not imply quantum correctness

An affine type prevents source-level copying of a register handle. It does not certify gate fidelity, calibration, randomness quality, measurement integrity, or the absence of hardware side channels.

---

## 12.4 Adversarial failure cases

A serious test campaign should include:

- deeply nested syntax causing parser recursion pressure;
- extremely long acyclic call chains;
- nonterminating loops;
- divisions by zero;
- invalid logarithm and square-root domains;
- overflow to infinity;
- NaN comparison behavior;
- malformed manually constructed SSA;
- forged phi predecessor lists;
- collisions between host-provided names and runtime symbols;
- hostile or oversized source files;
- floating-point event crossings extremely close to step boundaries;
- observer configurations approaching a communication horizon;
- cancellation in very small inward Minkowski travel times.

The prototype accepts only its own generated IR as trusted input. It is not an adversarially hardened IR loader.

---

## 12.5 What production-grade implementation would require

At minimum:

1. A versioned normative language specification.
2. A conformance test suite.
3. Source spans and professional diagnostics.
4. A standalone IR verifier.
5. A real native backend.
6. Translation validation or verified lowering for critical transformations.
7. Shape-polymorphic tensor analysis.
8. Ownership and effect checking.
9. Correct forward- and reverse-mode AD transformations.
10. Explicit deterministic and relaxed floating-point modes.
11. Accelerator memory planning and transfer scheduling.
12. Capability enforcement at every foreign-function boundary.
13. Quantum backend contracts and statistical validation.
14. Robust event detection for general trajectories.
15. Independent numerical reference implementations.
16. Property-based, differential, fuzz, and metamorphic testing.
17. Benchmarking against established systems.
18. Reproducible execution environments and captured run artifacts.

None of these should be hidden behind the phrase “the compiler handles it.”

---

## 12.6 Comparison with established approaches

| Area | Established approaches | Aether-Ω artifact |
|---|---|---|
| Ownership and memory safety | Rust and related ownership systems | Proposed affine/resource discipline; not implemented in scalar prototype |
| Tensor compilation | XLA, MLIR-based systems, TVM | No tensor backend |
| Differentiable programming | JAX, PyTorch, Enzyme, differentiable language research | Native syntax/semantics proposal; no AD pass |
| Numerical computing | Julia, C++, Fortran, Python scientific stack | Educational scalar interpreter |
| GPU programming | CUDA, HIP, Triton, SYCL | Scheduling design only |
| Quantum programming | Q#, Qiskit, Cirq, PennyLane and related systems | Hybrid type design and valid circuit examples; no quantum runtime |
| Formal verification | Lean, Coq, F*, Dafny, Why3, SPARK | Paper argument and contract design; no proof engine |
| Relativistic ray tracing | Established geodesic and numerical-relativity codes | Exact flat background with one-dimensional null dynamics |

The artifact is not competitive with these systems in performance, maturity, or verified assurance.

Its value is narrower and concrete: it is a self-contained example of how language semantics, SSA compilation, numerical integration, exact physical invariants, and honest implementation boundaries can fit together without conflating a proposed architecture with completed engineering.

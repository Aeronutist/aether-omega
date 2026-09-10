# Aether-Ω

An experimental programming-language design, scalar compiler, and
relativistic laser-communication simulation.

## Implemented prototype

- Lexer and recursive-descent parser
- Scalar type checking and semantic analysis
- SSA intermediate representation with phi nodes
- LLVM-like textual IR generation
- SSA interpreter
- Rindler-observer communication simulation
- RK4 integration and convergence checks
- ASCII frequency plots and spacetime animation

## Requirements

Python 3.10 or later. No third-party packages are required.

## Run

```bash
python3 aether_omega.py
```

For terminal animation:

```bash
python3 aether_omega.py --animate
```

On Windows, you may need to use `python` or `py` instead of `python3`.

The program writes an `aether_demo.ll` file and prints numerical
validation results and ASCII frames.

The generated IR resembles LLVM IR but is an educational dialect,
not LLVM-compatible assembly.

## Implementation scope

The executable implements a scalar subset of Aether-Ω.

Tensor types, automatic differentiation, differential geometry types,
formal verification, capability security, heterogeneous scheduling,
and quantum-classical types are language-design proposals. They are
not implemented by this prototype.

## Physics model

The simulation models two observers in the same Born-rigid Rindler
congruence in flat Minkowski spacetime.

In units where c = 1:

- Observer A has Rindler radius 1 and proper acceleration 1.
- Observer B has Rindler radius 2 and proper acceleration 1/2.
- The exact Rindler light-travel interval is ln(2).
- The A-to-B frequency ratio is 1/2.
- The B-to-A frequency ratio is 2.

The Rindler gravitational redshift and inertial Doppler calculation
describe the same frequency ratio, not two independent corrections.

## Documentation

See [PAPER.md](PAPER.md) for the language design, mathematical
formulation, numerical method, and limitations.

## Validation

The program includes compiler checks, numerical reference comparisons,
and a convergence check. The GitHub Actions workflow runs these checks
on each push and pull request.

Analytic reference values in the paper are not a captured execution
transcript. Consult a successful workflow run for execution evidence.
## Interactive website

An interactive Streamlit interface is included in `app.py`.

It provides:

- compiler execution and validation;
- convergence tables;
- frequency and coordinate-travel-time charts;
- ten selectable ASCII spacetime frames;
- generated IR;
- downloadable numerical samples and execution logs.

The website executes only the bundled benchmark program.

## Browser-only deployment

1. Fork or create a copy of this repository.
2. Confirm that GitHub Actions passes.
3. Sign in to Streamlit Community Cloud.
4. Select the repository and the `main` branch.
5. Set the application entrypoint to `app.py`.
6. Deploy.

## Validation status

Consult the repository's Actions tab for actual execution evidence.
The paper's analytic reference values are not a captured run transcript.

## Project status

Experimental scalar prototype.

The broader Aether-Ω language facilities remain design proposals.
This project is not a production compiler or a machine-verified system.

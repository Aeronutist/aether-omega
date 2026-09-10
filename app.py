"""Browser UI for the Aether-Omega scalar compiler and Rindler model."""

from contextlib import redirect_stdout
import io
import math

import pandas as pd
import streamlit as st

import aether_omega as ao


st.set_page_config(
    page_title="Aether-Ω | Rindler Communication",
    page_icon="🚀",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def run_experiment():
    """Compile and validate the fixed, bundled scientific program.

    No visitor-supplied source code is executed.
    Cached results contain only serializable data.
    """
    log = io.StringIO()

    with redirect_stdout(log):
        program = ao.compile_source(ao.PHYSICS)
        ao.compiler_tests(program)

        vm = ao.VM(program)
        measurements = ao.convergence(vm)
        ao.numerical_report(vm, measurements)
        ao.frequency_plots(vm, measurements)

        print("\nAll included validation checks passed.")

    ir = ao.ir_text(program)

    convergence_rows = []
    for direction, label in ((1.0, "A → B"), (-1.0, "B → A")):
        previous_error = None

        for steps in (512, 1024, 2048):
            delay = measurements[(steps, direction)]
            error = abs(delay - math.log(2.0))

            ratio = (
                previous_error / error
                if previous_error is not None and error > 0
                else None
            )

            convergence_rows.append(
                {
                    "Direction": label,
                    "Integration steps": steps,
                    "Numerical delay": delay,
                    "Absolute delay error": error,
                    "Refinement ratio": ratio,
                }
            )
            previous_error = error

    # Evaluate the compiled scalar functions over 512 emission intervals.
    sample_rows = []

    for direction, label in ((1.0, "A → B"), (-1.0, "B → A")):
        delay = measurements[(512, direction)]
        emitter_radius = 1.0 if direction > 0 else 2.0

        for i in range(513):
            eta = 2.0 * i / 512.0

            sample_rows.append(
                {
                    "Direction": label,
                    "Emission rapidity": eta,
                    "Emitter proper time": emitter_radius * eta,
                    "Receiver proper time": vm.call(
                        "receiver_tau", eta, delay, direction
                    ),
                    "Minkowski travel time": vm.call(
                        "lag", eta, delay, direction
                    ),
                    "Received/emitted frequency": vm.call(
                        "frequency", delay, direction
                    ),
                }
            )

    # The original drawing routine uses analytic photon characteristics.
    frames = []
    for i in range(10):
        eta = 0.2 * i
        frames.append(
            {
                "eta": eta,
                "viewport": ao.minkowski_frame(vm, eta),
                "A_t": vm.call("world_t", 1.0, eta),
                "A_x": vm.call("world_x", 1.0, eta),
                "B_t": vm.call("world_t", 2.0, eta),
                "B_x": vm.call("world_x", 2.0, eta),
            }
        )

    return {
        "log": log.getvalue(),
        "ir": ir,
        "convergence": pd.DataFrame(convergence_rows),
        "samples": pd.DataFrame(sample_rows),
        "frames": frames,
    }


st.title("Aether-Ω")
st.subheader("Interactive compiler prototype and Rindler communication model")

st.info(
    "Experimental research prototype. The executable implements a scalar "
    "language subset—not the proposed tensor, autodiff, quantum, GPU, "
    "capability-security, or formal-verification backends."
)

with st.sidebar:
    st.header("Experiment")
    st.write("Natural units: c = 1")
    st.write("Ship A: radius 1, proper acceleration 1")
    st.write("Ship B: radius 2, proper acceleration 1/2")
    st.caption(
        "The observer configuration is fixed to the validated benchmark. "
        "Changing parameters requires generalizing the solver and its tests."
    )

    selected_direction = st.selectbox(
        "Communication direction",
        ["A → B", "B → A"],
    )

    st.divider()
    st.write("Propagation resolutions: 512, 1024, 2048")
    st.write("Emission sampling: 512 intervals per direction")
    st.caption(
        "The 512 propagation steps cover an auxiliary interval [0, 8]. "
        "Only approximately 44–45 steps precede first reception at the "
        "coarsest resolution."
    )

try:
    with st.spinner("Compiling source and checking the numerical model…"):
        results = run_experiment()
except Exception as exc:
    st.error(
        "Compilation or numerical validation failed. "
        "This run must not be reported as successful."
    )
    st.exception(exc)
    st.stop()

st.success(
    "The bundled compiler tests and numerical validation checks passed "
    "for the run that produced these results."
)
st.caption(
    "Successful results are cached by Streamlit and may be reused across "
    "visits. Passing these checks is not a formal proof of correctness."
)

metric_a, metric_b, metric_c = st.columns(3)
metric_a.metric("Exact A → B frequency ratio", "0.5")
metric_b.metric("Exact B → A frequency ratio", "2.0")
metric_c.metric("Exact Rindler flight interval", f"{math.log(2):.10f}")

overview, numerical, viewport, compiler, science = st.tabs(
    ["Overview", "Numerical results", "Spacetime viewport", "Compiler", "Science"]
)

with overview:
    st.markdown(
        """
### What this website actually does

1. Parses the bundled Aether-Ω source.
2. Checks scalar types and function calls.
3. Lowers the program into SSA with phi nodes.
4. Executes that SSA using the Python interpreter backend.
5. Computes numerical light-flight intervals using RK4.
6. Checks convergence against the analytic result.
7. Displays tables, charts, and ASCII spacetime frames.

The UI is Python/Streamlit. The core numerical functions are executed
through the bundled Aether-Ω compiler and SSA interpreter.

### What it does not do

It does not execute arbitrary visitor code, implement quantum hardware,
simulate curved spacetime, or provide a production compiler.
"""
    )

    st.latex(
        r"\frac{\nu_r}{\nu_e}=\frac{\rho_e}{\rho_r}"
        r"=\exp[-s(\eta_r-\eta_e)]"
    )

    st.warning(
        "Rindler gravitational redshift and inertial Doppler shift are "
        "two descriptions of the same frequency ratio. They must not "
        "be multiplied as independent corrections."
    )

with numerical:
    st.header("Convergence")

    st.dataframe(
        results["convergence"],
        hide_index=True,
        use_container_width=True,
    )

    error_plot = results["convergence"].pivot(
        index="Integration steps",
        columns="Direction",
        values="Absolute delay error",
    )
    st.line_chart(error_plot)

    st.caption(
        "Fourth-order convergence predicts an error reduction near 16 "
        "when the step size is halved, before floating-point error dominates."
    )

    selected = results["samples"][
        results["samples"]["Direction"] == selected_direction
    ].copy()

    st.header(f"Frequency ratio: {selected_direction}")

    frequency_plot = selected.set_index("Emitter proper time")[
        ["Received/emitted frequency"]
    ]
    st.line_chart(frequency_plot)

    st.caption(
        "The flat frequency curve is physically correct for this stationary "
        "Rindler configuration. The plotted value uses the numerical delay "
        "in the inertial Doppler formula."
    )

    st.header("Minkowski coordinate light-travel time")

    travel_plot = selected.set_index("Emitter proper time")[
        ["Minkowski travel time"]
    ]
    st.line_chart(travel_plot)

    st.caption(
        "This is a difference in Minkowski coordinate time, not the elapsed "
        "proper time of a single clock carried between emission and reception."
    )

    st.dataframe(selected, hide_index=True, use_container_width=True)

    st.download_button(
        "Download all numerical samples as CSV",
        data=results["samples"].to_csv(index=False),
        file_name="aether_numerical_samples.csv",
        mime="text/csv",
    )

with viewport:
    st.header("ASCII spacetime viewport")

    st.write(
        "Scrub through ten sequential frames. Coordinates use a common "
        "Rindler-time slice, not a common Minkowski-time slice."
    )

    frame_number = st.slider(
        "Frame",
        min_value=0,
        max_value=9,
        value=0,
        step=1,
    )

    frame = results["frames"][frame_number]
    st.code(frame["viewport"], language="text")

    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Ship": "A",
                    "Rindler eta": frame["eta"],
                    "Minkowski t": frame["A_t"],
                    "Minkowski x": frame["A_x"],
                    "y": 0.0,
                    "z": 0.0,
                },
                {
                    "Ship": "B",
                    "Rindler eta": frame["eta"],
                    "Minkowski t": frame["B_t"],
                    "Minkowski x": frame["B_x"],
                    "y": 0.0,
                    "z": 0.0,
                },
            ]
        ),
        hide_index=True,
        use_container_width=True,
    )

    st.caption(
        "The viewport uses analytic photon characteristics and exact "
        "observer coordinate formulas. It illustrates the physical "
        "solution; it is not a visualization of RK4 error."
    )

    with st.expander("Show all ten frames"):
        for number, item in enumerate(results["frames"]):
            st.markdown(f"**Frame {number:02d}**")
            st.code(item["viewport"], language="text")

    all_frames = "\n\n".join(
        f"FRAME {number:02d}\n{item['viewport']}"
        for number, item in enumerate(results["frames"])
    )
    st.download_button(
        "Download ASCII frames",
        data=all_frames,
        file_name="aether_frames.txt",
        mime="text/plain",
    )

with compiler:
    st.header("Aether-Ω source")
    st.code(ao.PHYSICS, language="text")

    st.header("Generated SSA / LLVM-like text")
    st.caption(
        "Educational textual IR. It is not claimed to be accepted by LLVM."
    )
    st.code(results["ir"], language="text")

    st.download_button(
        "Download generated IR",
        data=results["ir"],
        file_name="aether_demo.ll",
        mime="text/plain",
    )

    st.header("Captured execution log")
    st.code(results["log"], language="text")

    st.download_button(
        "Download validation log",
        data=results["log"],
        file_name="aether_validation.txt",
        mime="text/plain",
    )

with science:
    st.header("Mathematical model")

    st.latex(r"ds^2=-dt^2+dx^2+dy^2+dz^2")
    st.latex(r"t=\rho\sinh\eta,\qquad x=\rho\cosh\eta")
    st.latex(r"ds^2=-\rho^2d\eta^2+d\rho^2+dy^2+dz^2")
    st.latex(r"d\tau=\rho\,d\eta,\qquad a=\frac{1}{\rho}")
    st.latex(r"\frac{d\rho}{d\eta}=s\rho,\qquad \Delta\eta=\ln 2")
    st.latex(
        r"\Delta t_{A\to B}=\frac{3}{2}e^{\eta_e},\qquad "
        r"\Delta t_{B\to A}=\frac{3}{4}e^{-\eta_e}"
    )

    st.markdown(
        """
### Interpretation

The metric is flat. “Gravitational redshift” refers to the lapse
difference in accelerated coordinates, not spacetime curvature.

The observers share a Rindler horizon. Arbitrary accelerating
worldlines need not have this communication behavior.

### Numerical scope

RK4 integrates a radial null characteristic. Observer worldlines
and coordinate transformations are analytic inputs.

The source samples continuous communication at 513 emission points.
It does not solve Maxwell's equations or propagate an optical field.

### Verification scope

The included tests check selected compiler and physical properties.
The Python implementation and compilation pipeline are not
machine-verified.
"""
    )

st.divider()
st.caption(
    "Aether-Ω experimental prototype · "
    "Streamlit frontend · Python scalar compiler backend"
)

# Quantum Computing: From Circuit Model to Reproducible Evaluation

## Problem Framing: What Is Worth Quantizing?

A workload is a credible quantum candidate only when success can be measured end to end. Before choosing an algorithm, define the problem, the classical reference, and the resource budget. This prevents an impressive circuit complexity from masking expensive data loading, output conversion, or repeated executions.

### 1. Define the decision or sampling contract

Write the contract before selecting the quantum algorithm:

```text
Input:        <schema, units, precision, instance distribution>
Output:       <value, certificate, or probability distribution>
Classical baseline: <algorithm, implementation, hardware>
Success:      <accuracy/error bound, latency, memory limit>
```

For a decision problem, specify whether the output is `true`/`false`, an optimum, or a bounded approximation. For a sampling problem, define the target distribution and acceptable divergence. Record the input-encoding and output-decoding costs as part of the baseline because they can eliminate an apparent quantum advantage.

A useful criterion is comparative rather than absolute: for a fixed benchmark suite, the quantum pipeline must meet the accuracy requirement with lower p95 wall-clock time than the baseline within a stated memory limit.

### 2. Separate algorithmic from hardware speedup

Algorithmic speedup concerns how work grows with problem size; hardware speedup concerns measured time on a particular machine and workload. Track both:

| Metric | What to record |
|---|---|
| Classical runtime and memory | p50/p95 time, peak memory, solver version, and hardware |
| Quantum circuit depth | logical depth, qubit count, gate count, and connectivity after compilation |
| Logical qubits | qubits required by the algorithm, excluding temporary physical-qubit expansion |
| Expected repetitions | expected shots, failed executions, and error-recovery attempts |

Model expected execution cost explicitly:

```text
E[T_quantum] = T_compile + E[R] × E[S] × T_execution
```

Here, `S` is the number of shots and `R` includes retries or recovery rounds. Compare algorithmic scaling only when input and output requirements are equivalent. Compare hardware speedup using the same instances, precision, quality threshold, and complete pipeline.

### 3. Classify the task and name a verifier

| Classification | Requirement | Small-instance verifier |
|---|---|---|
| Exact | Return the exact optimum or property | Brute force, dynamic programming, or an exact solver |
| Approximate | Guarantee a bound on error or approximation ratio | Compare against exact results within the allowed tolerance |
| Sampling | Produce samples close to a target distribution | Compare moments, marginals, or total variation distance |

Use an independent classical verifier for every small test instance. It should check both correctness and resource accounting. If no efficient verifier exists even for small cases, a quantum result may be impossible to validate reliably.

### 4. Set a go/no-go threshold

Define the decision rule before running experiments. For example:

```text
GO if:
  quality ≥ Q_threshold
  E[T_quantum] ≤ 0.8 × T_baseline
  peak memory ≤ M_limit
  confidence interval excludes no-speedup advantage
```

The quantum timing must include compilation, circuit execution, readout, shots, retries, and error-recovery overhead. Freeze the instance distribution, baseline implementation, precision, and threshold so later results are not selected to pass.

Reject the candidate when speedup disappears after full-pipeline accounting, when required qubits exceed the fault-tolerant budget, or when the verifier cannot establish the claimed accuracy. Those outcomes distinguish a genuine quantum opportunity from a generic performance claim.

## Build the Circuit Model: Qubits, Gates, and Measurement

### State vectors and entanglement

An $n$-qubit gate-based program is represented by a normalized vector in a $2^n$-dimensional complex vector space:

\[
|\psi\rangle=\sum_{x=0}^{2^n-1}\alpha_x|x\rangle,
\qquad
\sum_x |\alpha_x|^2=1.
\]

For two qubits, the tensor product combines individual states:

\[
(\alpha|0\rangle+\beta|1\rangle)\otimes(\gamma|0\rangle+\delta|1\rangle)
=
\alpha\gamma|00\rangle+\alpha\delta|01\rangle
+\beta\gamma|10\rangle+\beta\delta|11\rangle.
\]

The Bell state

\[
|\Phi^+\rangle=\frac{|00\rangle+|11\rangle}{\sqrt{2}}
\]

cannot be written as a product of two single-qubit states. If

\[
|\Phi^+\rangle=(a_0|0\rangle+a_1|1\rangle)\otimes(b_0|0\rangle+b_1|1\rangle),
\]

then its coefficients would be

\[
a_0b_0,\quad a_0b_1,\quad a_1b_0,\quad a_1b_1.
\]

The Bell coefficients are $(1/\sqrt2,0,0,1/\sqrt2)$. Since $a_0b_0$ and $a_1b_1$ are nonzero, all four factors must be nonzero, making the middle coefficients impossible to make zero. The qubits are therefore entangled rather than independently prepared.

### Gates, measurement, and depth

A quantum gate is a unitary matrix $U$, satisfying $U^\dagger U=I$. Unitary operations preserve normalization and are reversible. Common gates include

\[
H=\frac{1}{\sqrt2}
\begin{pmatrix}
1&1\\
1&-1
\end{pmatrix},
\qquad
Z=
\begin{pmatrix}
1&0\\
0&-1
\end{pmatrix}.
\]

Measuring a qubit in the computational basis applies the Born rule. For

\[
|\psi\rangle=\alpha|0\rangle+\beta|1\rangle,
\]

the outcomes are

\[
P(0)=|\alpha|^2,\qquad P(1)=|\beta|^2.
\]

After an ideal measurement, the qubit collapses to the observed basis state.

Circuit depth is the longest sequence of gates along any qubit wire. The following circuit has gate depth 3; a framework that counts measurement as a layer may report depth 4.

\[
|0\rangle
\xrightarrow{H}
\frac{|0\rangle+|1\rangle}{\sqrt2}
\xrightarrow{Z}
\frac{|0\rangle-|1\rangle}{\sqrt2}
\xrightarrow{H}
|1\rangle.
\]

The $Z$ gate introduces a relative phase. The final $H$ then causes destructive interference for outcome 0 and constructive interference for outcome 1, changing the probabilities from $P(1)=1/2$ without $Z$ to $P(1)=1$ with $Z$.

### Circuit diagram and implementation

A complete circuit records its qubits, gates, classical outputs, and shot count:

```text
q0 ──H────Z────H────M────▶ c0
                         shots = 1024
```

Here, `M` is the measurement operation and `c0` is the classical bit receiving its result. The equivalent Qiskit implementation is:

```python
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

shots = 1024

qc = QuantumCircuit(1, 1)
qc.h(0)
qc.z(0)
qc.h(0)
qc.measure(0, 0)

counts = (
    AerSimulator()
    .run(qc, shots=shots)
    .result()
    .get_counts()
)

print(counts)  # {'1': 1024}
```

The diagram maps directly to the code:

- `q0` is qubit index 0 in `QuantumCircuit(1, 1)`.
- `H`, `Z`, and `H` are the three calls to `qc.h(0)` and `qc.z(0)`.
- `M` is `qc.measure(0, 0)`.
- `c0` is classical bit index 0.
- `shots = 1024` controls the number of sampled executions.

The ideal simulator returns all 1024 shots as `1`. Real hardware can produce occasional errors, so shot counts are statistical rather than guaranteed to be deterministic.

### No-cloning, irreversibility, and termination

No-cloning states that no physical operation can copy an arbitrary unknown quantum state. A universal cloning unitary would require

\[
U|\psi\rangle|0\rangle=|\psi\rangle|\psi\rangle
\]

for every $|\psi\rangle$. Preserving inner products then requires

\[
\langle\psi|\phi\rangle
=
\langle\psi|\phi\rangle^2,
\]

which is impossible for distinct, non-orthogonal states. Known basis states can be copied with a CNOT, but an unknown superposition cannot.

Unitary gates are reversible, while measurement is not. Measurement maps many possible input amplitudes to the same classical outcome and discards the original coherence. In the circuit above, `qc.measure(0, 0)` is the terminal quantum operation: qubit `q0` collapses to `|0>` or `|1>`, and the result is written to classical bit `c0`.

The classical bit contains the measurement outcome, not the original amplitudes. A mid-circuit measurement can enable classically conditioned operations, but the measured qubit can no longer participate in coherent quantum evolution.

## 3. Implement a Minimal Working Example

### 3.1 Build and run the Bell-state circuit

The following Qiskit circuit prepares \(|00\rangle\), applies `H` to qubit 0, and applies `CX` from qubit 0 to qubit 1. This creates the Bell state:

\[
|\Phi^+\rangle=\frac{|00\rangle+|11\rangle}{\sqrt{2}}.
\]

```python
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Statevector

# Prepare |00>, apply H and CX, and measure both qubits.
qc = QuantumCircuit(2, 2, name="bell")
qc.h(0)
qc.cx(0, 1)

# Ideal statevector.
state = Statevector.from_instruction(qc)
print("Statevector:", np.round(state.data, 3))

# Run on an ideal simulator backend.
backend = AerSimulator()
compiled = transpile(qc, backend)

result = backend.run(
    compiled,
    shots=10_000,
    seed_simulator=12345,  # Makes the example reproducible.
).result()

counts = result.get_counts(compiled)
print(counts)
```

The expected statevector, ordered as \(|00\rangle, |01\rangle, |10\rangle, |11\rangle\), is:

```text
[0.5+0.j 0+0.j 0+0.j 0.5+0.j]
```

The simulator should return only `00` and `11`, each with approximately 5,000 shots.

### 3.2 Validate the counts with a confidence interval

Each Bell-state bitstring follows a binomial distribution with \(p=0.5\). With 10,000 shots, the standard error is:

\[
\sqrt{\frac{0.5(1-0.5)}{10000}} = 0.005.
\]

A normal-approximation 95% confidence interval has half-width \(1.96 \times 0.005 \approx 0.0098\), or approximately 49.02% to 50.98% for each marginal outcome.

```python
shots = 10_000
freq_00 = counts.get("00", 0) / shots
freq_11 = counts.get("11", 0) / shots

z = 1.96
margin = z * np.sqrt(0.5 * 0.5 / shots)
lower = 0.5 - margin
upper = 0.5 + margin

print(f"freq(00) = {freq_00:.4f}")
print(f"freq(11) = {freq_11:.4f}")
print(f"95% CI = [{lower:.4f}, {upper:.4f}]")

assert 0 <= counts.get("01", 0) + counts.get("10", 0) <= 2
assert lower <= freq_00 <= upper
assert lower <= freq_11 <= upper
```

The small tolerance accounts for ordinary finite-shot fluctuations. A real backend may also introduce gate and readout errors, so larger deviations can indicate hardware noise or transpilation effects.

### 3.3 Inspect amplitudes and distinguish pure from mixed states

The statevector shows the two nonzero amplitudes directly. A density matrix additionally exposes coherence between \(|00\rangle\) and \(|11\rangle\):

```python
from qiskit.quantum_info import DensityMatrix, state_fidelity

rho_bell = DensityMatrix.from_instruction(qc)
print(np.round(rho_bell.data, 3))
```

The ideal Bell-state density matrix is:

```text
[[0.5 0.  0.  0.25]
 [0.  0.  0.  0.  ]
 [0.  0.  0.  0.  ]
 [0.25 0.  0.  0.5 ]]
```

The diagonal contains the measurement probabilities. The off-diagonal terms are coherence terms; they distinguish the coherent superposition from a classical mixture with the same diagonal.

```python
def diagnostics(rho):
    rho = np.asarray(rho)
    return {
        "purity": float(np.trace(rho @ rho).real),
        "fidelity_to_bell": float(np.real(state_fidelity(rho, state)).real),
        "coherence": float(np.real(rho[0, 3])),
    }

print(diagnostics(rho_bell))
```

For comparison, a maximally mixed state has purity \(1/4\), zero coherence, and fidelity \(1/2\) with the Bell state.

A simple noisy simulation can be checked in the same way:

```python
from qiskit_aer.noise import NoiseModel, depolarizing_error

noise_model = NoiseModel()
noise_model.add_all_qubit_quantum_error(
    depolarizing_error(0.05, 1), ["h"]
)
noise_model.add_all_qubit_quantum_error(
    depolarizing_error(0.10, 2), ["cx"]
)

noisy_qc = qc.copy()
noisy_qc.save_density_matrix()

noisy_backend = AerSimulator(noise_model=noise_model)
noisy_result = noisy_backend.run(noisy_qc).result()
rho_noisy = DensityMatrix(noisy_result.data(0)["density_matrix"])

print(diagnostics(rho_noisy))
```

For experimental hardware, use state tomography to reconstruct \(\rho\):

```python
from qiskit.quantum_info.tomography import StateTomography

tomography = StateTomography(qc)
rho_tomo = tomography.run(tomography, backend=backend).reduce()
```

Tomography is useful when the state cannot be inspected directly, but it requires many measurement settings and scales poorly with qubit count. Direct density-matrix simulation is cheaper for small circuits.

### 3.4 Add a parameterized gate angle and plot interference

Parameterize the rotation before the CNOT gate:

```python
from qiskit.circuit import Parameter
import matplotlib.pyplot as plt

theta = Parameter("theta")
angle_qc = QuantumCircuit(2, 2)
angle_qc.h(0)
angle_qc.ry(theta, 0)
angle_qc.cx(0, 1)

angles = np.linspace(-np.pi, np.pi, 401)
p00 = []
p11 = []

for value in angles:
    bound = angle_qc.assign_parameters({theta: value})
    probabilities = Statevector.from_instruction(bound).probabilities()
    p00.append(probabilities[0])  # P(00)
    p11.append(probabilities[3])  # P(11)

plt.plot(angles, p00, label="P(00)")
plt.plot(angles, p11, label="P(11)")
plt.xlabel("theta (radians)")
plt.ylabel("Probability")
plt.title("Angle-dependent interference")
plt.legend()
plt.grid(True)
plt.show()
```

The resulting probabilities are:

\[
P(00)=\cos^2(\theta/2), \qquad
P(11)=\sin^2(\theta/2).
\]

At \(\theta=0\), the circuit returns the Bell-state distribution. At \(\theta=\pi\), it returns \(|11\rangle\) with probability 1. The sinusoidal curves make the angle-dependent interference visible; a purely classical mixture would not reproduce this continuous transition.

## 4. From Logical Circuits to Hardware: Algorithms, Noise, and Cost — Performance

Evaluate a quantum workload at four distinct layers: the logical algorithm, the compiled circuit, the fault-tolerant resource estimate, and the billable execution. A polynomial logical complexity does not imply near-term feasibility, while a shallow variational circuit may still be expensive in shots or queue time. Compare workloads using the same input size, precision, confidence target, and classical baseline.

### 1. Compare algorithms by workload assumptions

The order below is a taxonomy, not a ranking. Each algorithm solves a different problem, and its advantage depends on oracle costs, precision, hardware fidelity, and the quality of the classical method used for comparison.

| Algorithm/workload | Input model | Logical complexity | Error tolerance | Classical baseline |
|---|---|---|---|---|
| **Shor** | An $n$-bit integer $N$; the quantum portion performs modular exponentiation and phase estimation. | Roughly $O(n^3)$ elementary operations under common gate models, ignoring lower-order arithmetic factors. | Requires very low logical error rates and fault-tolerant magic-state production. A noisy, shallow implementation does not provide a useful factorization. | General Number Field Sieve, whose runtime is sub-exponential in $n$. Compare at equal bit length and verification cost. |
| **Grover** | A black-box oracle over $N$ items with $M$ marked solutions. | $O(\sqrt{N/M})$ oracle queries, or $O(\sqrt N)$ for one solution. Total cost also includes constructing and uncomputing the oracle. | The oracle must remain coherent. Moderate noise can erase the quadratic query advantage even when individual gates look acceptable. | Classical search is $O(N/M)$ queries. Include any classical preprocessing and oracle-evaluation cost. |
| **Quantum simulation** | A Hamiltonian, initial state, evolution time $t$, and observables. Access may be local, sparse, or via more powerful oracles. | Depends on locality, allowed Hamiltonian access, $t$, and precision $\varepsilon$. Product formulas have larger error terms; qubitization can give near-linear time dependence and polylogarithmic precision dependence under suitable assumptions. | Noisy or analog execution may be useful for qualitative observables. High-precision digital simulation needs error correction and a logical error budget. | Exact diagonalization grows exponentially; tensor networks, quantum Monte Carlo, density functional theory, and configuration interaction may be effective for restricted cases. |
| **VQE / QAOA** | VQE uses a Hamiltonian, ansatz, and classical parameters; QAOA uses a graph or cost Hamiltonian and $p$ alternating layers. | VQE has no general asymptotic advantage guarantee. QAOA uses $p$ layers and its quality is problem- and schedule-dependent. Optimization and oracle construction can dominate circuit depth. | These are candidates for noisy devices, but noise biases objectives, parameters can suffer barren plateaus, and deeper circuits eventually require logical error correction. | Compare with exact solvers for small instances and the best relevant classical heuristic at the same solution quality or approximation ratio. |
| **Sampling** | A circuit family generating bit strings, such as random-circuit, bosonic, or structured sampler outputs. | Hardness is usually conditional on assumptions such as anti-concentration and average-case hardness. The relevant resource is output fidelity, not only gate count. | Fidelity must remain above the point where the distribution is classically simulable or indistinguishable from noise. Errors accumulate across depth and qubits. | Exact simulation, tensor networks, Monte Carlo, and specialized classical samplers, depending on the circuit family. |

For a fair comparison, report the cost of preparing the input, implementing oracles, reading out results, and verifying the answer. A query-complexity advantage can disappear when the oracle is expensive, while a sampling advantage can disappear if the output distribution is too noisy to certify.

### 2. Compile for a target backend and measure the overhead

Compile separately for each backend, calibration snapshot, and routing policy. Record the backend ID, transpiler version, optimization level, random seed, and calibration time so the result is reproducible.

Capture the following before and after decomposition:

- Logical qubit count, including workspace and ancillas.
- Initial and final logical-to-physical layouts; a single static map can be misleading when routing changes during the circuit.
- Connectivity-induced SWAP count and SWAP depth, measured from the routing trace before SWAPs are decomposed.
- Native gate set, including gate durations and per-gate error rates.
- Transpiled total depth and two-qubit depth.
- Estimated success or failure probability for one complete circuit execution.

An illustrative report is:

```json
{
  "logical_qubits": 12,
  "physical_qubits": 19,
  "logical_to_physical": {
    "q0": 4, "q1": 5, "q2": 6, "q3": 9,
    "q4": 10, "q5": 11, "q6": 14, "q7": 15,
    "q8": 16, "q9": 19, "q10": 20, "q11": 21
  },
  "routing": {
    "connectivity": "heavy-hex",
    "swap_count": 86,
    "swap_depth": 41
  },
  "native_gates": ["rz", "sx", "x", "cz"],
  "transpiled_depth": 742,
  "two_qubit_depth": 301,
  "estimated_error_per_run": 0.519,
  "calibration_snapshot_id": "backend-2025-001"
}
```

A simple independent-error estimate is:

$$
p_{\mathrm{fail}} \approx 1-\exp\left(-\sum_i n_i p_i - m p_{\mathrm{readout}}\right),
$$

where $n_i$ is the count of native gate type $i$, $p_i$ is its calibrated error, and $m$ is the number of measured qubits. For example, 120 single-qubit gates at $10^{-3}$, 300 two-qubit gates at $2\times10^{-3}$, and 12 readouts at $10^{-3}$ give $\lambda=0.732$, an estimated success probability of $e^{-0.732}\approx48.1\%$, and failure probability about $51.9\%$.

This estimate is optimistic when errors are correlated. Leakage, crosstalk, measurement feedback, calibration drift, and idle errors can make the real failure rate higher. Report a range from repeated calibration snapshots and distinguish circuit failure from algorithmic failure.

### 3. Estimate fault-tolerant requirements

A fault-tolerant estimate should separate logical resources from physical implementation details.

| Quantity | What to estimate |
|---|---|
| Logical qubits | Algorithm qubits, routing workspace, measurement ancillas, and magic-state factory qubits. |
| Code distance | The smallest odd distance $d$ that meets the logical error target under the selected code and physical error model. |
| Physical qubits per logical qubit | Approximately $2d^2$ for a surface-code patch, before factories, buffers, and architecture-specific overhead. |
| T-count and T-depth | Total non-Clifford $T$ gates and the minimum number of sequential $T$ layers. T-depth constrains parallel factory scheduling. |
| Logical error rate | Per logical operation, including gates, measurements, resets, routing, and factory failures. |
| Wall-clock time | Data-circuit time, syndrome cycles, magic-state supply time, reset/scheduling overhead, and any cloud queue time. |

For an idealized surface-code model below threshold, a common approximation is:

$$
p_L(d)\approx 0.1\left(\frac{p_{\mathrm{phys}}}{p_{\mathrm{th}}}\right)^{(d+1)/2}.
$$

Choose $d$ so that $N_{\mathrm{ops}}p_L(d)\leq\varepsilon_{\mathrm{target}}$, where $N_{\mathrm{ops}}$ counts the logical operations that must succeed. The threshold and prefactor are model-dependent; use the code and architecture’s calibrated model rather than treating these values as universal.

For example, with target algorithm failure $\varepsilon_{\mathrm{target}}=10^{-6}$, $10^6$ logical operations, physical error $10^{-3}$, and idealized threshold $0.1$, distance 11 gives an approximate logical error near $10^{-13}$, while distance 9 gives about $10^{-11}$. With 100 logical data qubits, distance 11 implies roughly $100\times2\times11^2=24{,}200$ data qubits before factories and buffers.

Let $C_{\mathrm{logical}}$ be the scheduled logical cycle count, $r_{\mathrm{data}}$ the data-cycle rate, $N_T$ the T-count, and $R_T$ the magic-state throughput. A lower-bound runtime is:

$$
T_{\mathrm{wall}}\approx
\max\left(\frac{C_{\mathrm{logical}}}{r_{\mathrm{data}}},\frac{N_T}{R_T}\right)
+T_{\mathrm{scheduling}}+T_{\mathrm{queue}}.
$$

T-depth determines how many $T$ blocks can run in parallel; T-count determines how many must be supplied in total. If a workload has $N_T=10^8$, $D_T=10^5$, and factory throughput $10^6$ $T$ blocks/s, the factory supply lower bound is about 100 s. If the data circuit needs $10^6$ logical cycles at 1 $\mu$s each, it would take about 1 s, so factories dominate. Actual schedules, leakage handling, correlated errors, and factory failure rates can change both qubit count and time substantially.

### 4. Build a cost model and stop when additional shots add little value

Let $S$ be shots per circuit, $K$ the number of quantum evaluations in a hybrid loop, and $S_{\mathrm{total}}=\sum_{k=1}^{K}S_k$. A provider-specific cost model can be written as:

$$
C_{\mathrm{qpu}}=S_{\mathrm{total}}p_{\mathrm{shot}}
+\max(T_{\mathrm{exec}},T_{\mathrm{bill}})p_{\mathrm{minute}}
+C_{\mathrm{egress}}.
$$

Queue time may not be billable, but it is still an opportunity cost. Include calibration changes between batches, failed jobs, retries, and the cost of classical optimization.

| Execution mode | Shots | Queue time | Hardware price | Main cost driver |
|---|---:|---|---|---|
| **Simulator** | $S$ sampled shots, or no shot count for an exact statevector density calculation | Local or HPC queue; usually near-zero for small instances | CPU/GPU hours, memory, storage, and data movement | Memory grows exponentially with statevector width; tensor-network and noisy simulators add their own costs. |
| **Cloud QPU** | $S$ shots per circuit and calibration | Submission-to-result delay $Q(S)$, plus calibration and job retries | Per-shot and/or per-minute pricing, egress, and storage | Noise, limited parallelism, queue contention, and the number of circuits submitted. |
| **Hybrid classical–quantum** | $\sum_k S_k$ quantum shots across $K$ classical iterations | $\sum_k Q(S_k)$, often repeated many times | Classical compute plus QPU charges, egress, and storage | Repeated circuit compilation, parameter optimization, noisy objective estimates, and queue overhead. |

Use a stopping rule based on the metric that matters: energy error for VQE, approximation ratio for QAOA, fidelity or a distribution metric for sampling, and verification success for Shor.

1. Choose a minimum meaningful improvement $\delta$ and a confidence level, such as 95%.
2. Run increasing shot batches, for example 100, 400, 1600, and so on.
3. Estimate the improvement and its confidence interval after each batch.
4. Stop when the upper confidence bound on improvement is below $\delta$, or when marginal metric gain per dollar falls below a chosen threshold for two or three consecutive batches.
5. Stop earlier if calibration drift, leakage, or another systematic error dominates shot noise.

Shot noise decreases as $1/\sqrt S$: quadrupling shots only halves standard error. Therefore, additional shots are not worthwhile once they no longer improve the decision more than their compute, queue, and hardware cost. For variational algorithms, also stop when the classical optimizer stalls, but verify that the apparent plateau is not caused by noisy objective estimates.

### 5. Document security and privacy controls for cloud jobs

Treat the circuit, metadata, calibration context, and raw measurement results as potentially sensitive. A quantum circuit can reveal proprietary model structure, while job logs and output objects may expose private labels or business data.

| Control | Implementation | Verification |
|---|---|---|
| **Least-privilege credentials** | Use a dedicated service account or workload identity. Grant access only to the required backend, job namespace, result bucket, and KMS keys. Prefer short-lived tokens over shared API keys, rotate credentials, and disable interactive root access. | Review IAM policies, test denied access, audit token issuance, and rotate credentials after personnel or project changes. |
| **Encrypted storage and transport** | Enforce TLS 1.3 or the provider’s equivalent for uploads and downloads. Encrypt circuits, logs, intermediate data, and results at rest with AES-256 or an equivalent service, managed through KMS with separated data and key-admin roles. | Inspect encryption settings for buckets, volumes, backups, and snapshots; verify key rotation and access logs. |
| **Output access** | Keep result objects private by default. Use scoped IAM policies or short-lived signed URLs, expire downloads, enable object versioning or immutability where appropriate, and scan outputs for accidental secrets before sharing. | Test download permissions from an unprivileged identity and review access logs for unexpected reads or exports. |
| **Retention and deletion** | Define a lifecycle policy for raw circuits, logs, calibration snapshots, intermediate states, and final results. For example, delete raw payloads after 30 days and retain anonymized aggregates for 90 days, subject to legal and contractual requirements. Include backup deletion or expiration and document legal-hold exceptions. | Run deletion jobs, verify object and snapshot lifecycle rules, and obtain provider confirmation of deletion where the contract requires it. |
| **Audit and data residency** | Record job IDs, identities, source IPs, circuit hashes, backend versions, and result access events. Keep logs immutable for the required period and select regions that satisfy data-residency requirements. | Reconcile audit logs with job records and periodically test incident-response access. |

Do not assume that encryption alone provides isolation: cloud providers and administrators may still process data in memory, and logs can retain metadata after an object is deleted. Minimize uploaded data, avoid placing secrets in circuit names or metadata, and state explicitly whether the provider may retain job payloads, telemetry, or derived results after execution.

## Debug Noisy Runs and Measure What Matters

### 1. Build a reproducible execution record

Run the same logical circuit against an ideal simulator and the selected QPU with identical transpilation options. Preserve evidence in a run manifest rather than reconstructing it from dashboard screenshots.

```json
{
  "run_id": "qrun-2025-03-08-001",
  "backend": "ibm_quebec",
  "backend_version": "1.2.4",
  "simulator": "qsim-statevector",
  "simulator_version": "3.1.0",
  "random_seed": 1729,
  "shots": 4096,
  "transpiled_circuit": "run.qasm3",
  "calibration": "calibration-2025-03-08T10:15Z.json",
  "raw_counts": {
    "ideal": {"00": 4096},
    "qpu": {"00": 3912, "11": 184}
  }
}
```

Store the simulator’s raw counts, QPU response, calibration snapshot, backend name and version, transpiled circuit, seed, and provider job ID. If the QPU does not support seed control, record `null`, mark it unsupported, and retain the calibration timestamp and execution time. Keep raw responses unchanged; compute derived metrics from them.

### 2. Define metrics and acceptance thresholds

Calculate metrics from the preserved data before interpreting a pass or failure:

- **Success probability:** `target_counts / total_shots`.
- **Fidelity or accuracy:** use one explicit definition, such as state fidelity for a pure target state or classification accuracy over a benchmark set.
- **Readout error:** report the confusion matrix or average `0→1` and `1→0` error from contemporaneous calibration.
- **Shot standard deviation:** use the empirical standard deviation across independent circuit repeats; for a single binary outcome, the binomial estimate is `sqrt(p(1-p)/n)`.
- **Transpilation depth:** measure the depth of the exact circuit submitted to the backend, not the original logical circuit.
- **Job latency:** measure from accepted submission to terminal completion or failure.

Set thresholds before testing—for example, success probability ≥ 0.90, readout error ≤ 2%, transpiled depth ≤ 300, and p95 job latency ≤ 60 seconds. Record the threshold version and failed assertions. This prevents post hoc threshold selection and makes regressions comparable across calibrations and backend releases.

### 3. Attribute noise to preparation, gates, or measurement

Run three versions of each diagnostic circuit with the same transpilation and random seed:

```text
ideal → depolarizing noise → calibrated backend noise
```

Use density-matrix simulation for small circuits and tomography when reconstructing the actual state or process is necessary. Prepare known states to estimate preparation error, apply targeted gates and compare their process matrices with ideal operations, and prepare `|0⟩` and `|1⟩` to estimate measurement error. This separates state-preparation-and-measurement effects from gate fidelity instead of treating all deviations as one aggregate loss.

Depolarizing noise provides a controlled, repeatable baseline; calibrated noise adds realistic, time-dependent errors but requires a matching calibration snapshot. Tomography offers stronger diagnosis but scales poorly—full state tomography requires roughly `4ⁿ` measurement settings—so reserve it for small subsystems. Density matrices also consume `O(4ⁿ)` memory.

### 4. Exercise edge cases and verify clean failures

Include these cases in the test matrix:

1. **All-zero input:** establishes the lowest-noise baseline and exposes biased readout.
2. **Maximally mixed state:** use `I/d` in simulation; on hardware, approximate it with a documented randomized Pauli mixture and record that approximation.
3. **Disconnected qubits:** verify whether they remain idle, reset, or are omitted by the backend contract; an unsupported logical mapping is a configuration error, not a quantum result.
4. **Deterministic outcomes:** allow statistical tolerance and report confidence intervals rather than requiring identical counts in repeated runs.
5. **Circuits exceeding backend limits:** test maximum qubits, depth, width, job size, and shots where supported.

Record whether every failure is clean: the provider returns a documented error code, no partial results are exposed, and retrying does not duplicate charged work. Unexpected partial success, stale job status, or undocumented errors should be treated as harness failures.

### 5. Add structured logs and traces

Wrap compilation and execution with spans for circuit parsing, transpilation, calibration lookup, job submission, polling, and result decoding. Every event should include the run ID, backend, compiler version, calibration timestamp, job ID, seed, and trace ID. Log per-batch counts and completion status while preserving the original batch response.

```json
{"event":"batch.completed","run_id":"qrun-2025-03-08-001","job_id":"job-84f1","batch":3,"shots":512,"counts":{"00":497,"11":15}}
```

Retries must reuse the same trace ID and record attempt number and latency. Do not log secrets or unbounded circuit payloads. A reproducible failure record should allow another run to reconstruct the logical circuit, transpiled circuit, compiler settings, backend state, calibration, seed policy, and every execution batch.

## 6. Common Mistakes and How to Avoid Them

A credible quantum result must distinguish algorithmic behavior, simulator evidence, hardware evidence, and security controls. The following checks prevent common overclaims.

### 1. Rejecting “all inputs at once”

An \(n\)-qubit state contains amplitudes, but a circuit does not evaluate every input and return every answer. Gates transform amplitudes coherently; interference redistributes probability, and measurement returns one sample from that distribution.

For a four-state Grover example with marked state \(|11\rangle\):

```text
# Oracle: phase-flip |11>
H(q0); H(q1)
CNOT(q0,q1); Z(q1); CNOT(q0,q1)

# Diffusion: D = 2|s><s| - I
H(q0); H(q1); X(q0); X(q1)
CNOT(q0,q1); Z(q1); CNOT(q0,q1)
X(q0); X(q1); H(q0); H(q1)

measure(q0,q1)
```

| Circuit | \(P(00)\) | \(P(01)\) | \(P(10)\) | \(P(11)\) | Expected counts, 4096 shots |
|---|---:|---:|---:|---:|---|
| No oracle | 0.250 | 0.250 | 0.250 | 0.250 | 1024, 1024, 1024, 1024 |
| One Grover iteration | 0.0625 | 0.0625 | 0.0625 | 1.000 | 256, 256, 256, 4096 |

The oracle changes a phase; the diffusion operator converts that phase difference into amplitude interference. The observable change is the measurement distribution, not a simultaneous classical evaluation of all inputs.

### 2. Claiming speedup from a toy circuit

A small demo cannot establish a quantum speedup. Report:

1. **A classical baseline:** use the best relevant classical algorithm, the same problem definition, input distribution, accuracy target, and stopping criterion—not an unoptimized brute-force reference.
2. **Scaling:** evaluate multiple problem sizes and report both strong and weak scaling. A four-qubit runtime is not evidence of asymptotic behavior.
3. **Resource accounting:** record logical qubits, native gates, circuit depth, shots, memory, wall time, queue time, retries, and cloud cost. Separate algorithmic resources from transpiler and hardware overhead.
4. **Repeated-trial uncertainty:** run each size independently, preferably at least 30 times, and report a median with an interquartile range or confidence interval:

   \[
   T_Q(n)=\operatorname{median}_r(Q_r+E_r+C_r)
   \]

   where \(Q_r\), \(E_r\), and \(C_r\) are queue, execution, and egress times.

Queueing, warm caches, throttling, backend drift, and transpiler changes can dominate small jobs and create a false speedup. Report these components separately rather than hiding them in a single wall-clock number.

### 3. Treating statevectors as QPU evidence

A statevector is an exact ideal simulation. It does not include finite shots, decoherence, readout error, crosstalk, leakage, or calibration drift. Compare sources explicitly:

| Source | Shots | Noise assumptions | Evidence provided |
|---|---:|---|---|
| Ideal statevector | Not applicable | None; pure state | Exact ideal probabilities |
| Ideal shot simulator | Example: 4,096 | Noiseless gates | Sampling uncertainty only |
| Noisy simulator | Example: 4,096 | Supplied gate/readout/decoherence model | Prediction under that model |
| QPU | Example: 4,096 | Named backend, calibration timestamp, transpiled circuit | Evidence for that device and time window |

Compare ideal and noisy distributions with a metric such as total variation distance, and report the shot-count and noise-model assumptions. A noisy simulator is still not a QPU result unless its model has been independently validated against the target device. Watch for stale calibration data, unmodeled leakage, and different transpilation results.

### 4. Confusing physical and logical qubits

For a fault-tolerant workload, never report only the number of physical qubits. A rough surface-code estimate is:

\[
N_{\text{phys}} \approx L \cdot 2d^2 \cdot (1+\text{routing overhead})
\]

where \(L\) is the logical-qubit count and \(d\) is the code distance. For \(L=100\) and \(d=21\), one code block is roughly \(2d^2=882\) physical qubits, or 88,200 qubits before routing and auxiliary overhead.

Connectivity also matters. Map the logical interaction graph onto the hardware coupler graph, insert SWAPs for unsupported edges, and report the resulting routed depth and additional error-prone operations. An all-to-all logical graph on a nearest-neighbor line can add substantial routing overhead.

Estimate workload failure separately:

\[
p_L \approx A\left(\frac{p}{p_{\text{th}}}\right)^{(d+1)/2}, \qquad
p_{\text{fail}} \approx 1-(1-p_L)^{G_L}
\]

For example, with \(A=10\), \(p=10^{-3}\), \(p_{\text{th}}=10^{-2}\), and \(d=21\), \(p_L\approx10^{-10}\). For \(G_L=10^9\) logical operations, the independent-error estimate is about \(9.5\%\) failure. These numbers are illustrative; correlated errors, leakage, decoder failure, and qubit yield must be included in a production estimate.

### 5. Exposing secrets in jobs or cloud metadata

Use a concrete data-handling policy rather than relying on “secure defaults”:

- **Encryption:** use TLS 1.3 in transit and AES-256 or provider-managed equivalent encryption at rest. Prefer KMS envelope encryption and customer-managed keys when tenant isolation requires them.
- **Secrets and credentials:** keep passwords, API keys, and tokens in a secret manager, never in job bodies, tags, labels, descriptions, or logs. Use short-lived workload identity or OIDC tokens (for example, no longer than one hour), rotate them immediately on suspected exposure, and rotate retained API keys on a defined schedule such as every 90 days.
- **Access control:** grant least-privilege IAM roles per project or workload, require MFA for interactive access, restrict KMS permissions, and audit all job and metadata operations.
- **Metadata:** redact or encrypt tenant identifiers, source paths, resource names, and request parameters before upload. Cloud metadata can persist even after a job is deleted.
- **Deletion and retention:** define retention periods for raw jobs, results, versions, snapshots, caches, backups, and metadata. For example, retain raw artifacts for 30 days and aggregate metrics for one year, with legal holds and backup-lifecycle expiration. Verify purge completion and destroy key material according to the same schedule.

Logs, traces, retry payloads, ephemeral disks, and shared notebooks are common leakage paths. Disable verbose logging or redact data before it enters the cloud control plane.

## Production Checklist and Next Steps

Treat the prototype as an evaluation candidate, not a production system, until every claim can be regenerated from versioned inputs. Work through the checklist below and retain the evidence with each run.

### 1. Production-readiness checklist

- [ ] **Problem statement:** Define the input distribution, objective, target output, operating constraints, and what counts as a successful result.
- [ ] **Classical baseline:** Run the same inputs with the strongest reasonable exact, heuristic, or approximation method. Record accuracy, latency, memory, and cost under equivalent assumptions.
- [ ] **Circuit:** Version the logical circuit, gate set, qubit count, depth, ansatz, measurement map, and transpilation settings. Record any problem-specific encoding.
- [ ] **Backend:** Identify the provider, target, service version, execution mode, qubit mapping, gate set, and availability constraints.
- [ ] **Noise model:** Specify whether results use ideal simulation, a provider calibration, a synthetic model, or measured calibration data. Validate model error against recent backend data where possible.
- [ ] **Acceptance thresholds:** Set the minimum success probability, maximum runtime, maximum cost, and confidence level before reviewing results. Avoid moving the target after seeing the outcome.
- [ ] **Cost:** Include quantum execution, classical preprocessing and postprocessing, retries, storage, error mitigation, and—when relevant—error correction. Normalize cost per accepted solution.
- [ ] **Security:** Document data classification, access controls, secrets handling, network egress, model or IP restrictions, retention, and audit logging.
- [ ] **Reproducibility artifacts:** Retain the code, lockfiles, environment definition, dataset and hash, seeds, configuration, raw outputs, transformation code, and final report.

### 2. Define a reproducible run record

Create one immutable record per execution. A compact YAML representation is sufficient:

```yaml
run_id:
problem_id:
code_commit: "<full SHA>"
environment_lockfile:
  path: "environment.lock"
  sha256: "<hash>"
random_seed:
input_dataset:
  version:
  sha256: "<content hash>"
circuit:
  path:
  options:
backend:
  name:
  target:
  service_version:
  execution_mode:
calibration_snapshot:
  uri:
  sha256: "<snapshot hash>"
  acquired_at:
noise_model:
  name:
  version:
  parameters_sha256:
execution:
  shots:
  simulator_seed:
  transpile_seed:
raw_counts:
  uri:
  sha256: "<raw output hash>"
transformed_metrics:
  success_probability:
  confidence_interval_95:
  runtime_seconds:
  cost:
    quantum:
    classical:
    mitigation:
    total:
  overhead_vs_baseline:
```

Keep `raw_counts` byte-for-byte immutable. Derive `transformed_metrics` with versioned code; for a binary objective, use `successful_count / shots`, then apply the documented aggregation and confidence-interval method across the input set. This separates observations from interpretation and makes later corrections traceable.

### 3. Change one variable at a time

Run a baseline point, then vary exactly one factor while holding the commit, dataset, seed policy, backend configuration, and measurement procedure constant. Repeat across seeds when stochastic behavior matters.

| Variable | What to record | Important trade-off |
|---|---|---|
| Qubit count | Logical and physical qubits, mapping, success probability, and total cost | More qubits may reduce encoding complexity but increase exposure to noisy operations. |
| Circuit depth | Logical depth, compiled depth, success probability, and cost | Greater expressive power can improve accuracy while amplifying gate and idle errors. |
| Error mitigation | Method, extra circuits, extra shots, bias reduction, and cost multiplier | Mitigation can improve estimates but often increases execution cost substantially. |
| Shot count | Same circuit and noise conditions, success estimate, interval width, and cost | More shots reduce sampling variance roughly with `1/sqrt(shots)` but increase cost linearly. |

Also record calibration drift, backend queueing, transpiler changes, and failed executions. If a calibration changes mid-experiment, split the results into separate records rather than silently mixing snapshots.

### 4. Decision rule

Proceed only when the quantum candidate meets the acceptance threshold with auditable overhead, including classical work and mitigation or correction. Pause when evidence is incomplete—for example, because of calibration drift or insufficient repetitions—and schedule a controlled follow-up. Stop when the classical baseline or error-corrected cost dominates.

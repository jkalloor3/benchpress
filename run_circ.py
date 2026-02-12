from bqskit.ir.circuit import Circuit, CircuitGate
from bqskit.compiler.compile import _circuit_workflow
import sys
import pickle
import time
from pathlib import Path

from bqskit.compiler.compiler import Compiler

from bqskit.compiler.machine import MachineModel
from bqskit import enable_logging

enable_logging(False)

def launch_circ(circuit: Circuit,
                 model: MachineModel, 
                 num_3q_blocks: int,
                 output_file: str) -> None:
    '''
    Compile to a total synthesis error of 1e-4. This error is very low, and
    also is a (loose) upper bound on the error. Therefore, the output circuit
    is guaranteed to be precise.
    '''

    synthesis_epsilon = 1e-4 / num_3q_blocks

    synthesis_epsilon = min(synthesis_epsilon, 1e-6)

    workflow = _circuit_workflow(
        model,
        optimization_level=4,
        synthesis_epsilon=synthesis_epsilon,
        error_threshold=1e-4,
        seed=42
    )
    
    compiler = Compiler(num_workers=-1)
    start_time = time.time()
    compiled_circuit, data = compiler.compile(circuit, workflow, 
                                              request_data=True)
    compile_time = time.time() - start_time

    print(f"Compilation time: {compile_time:.2f} seconds")

    out_data = {
        'input_circuit': circuit,
        'compiled_circuit': compiled_circuit,
        'compile_time': compile_time,
        'compilation_data': data,
        'target_output_error': 1e-3,
        'synthesis_epsilon': synthesis_epsilon
    }

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    pickle.dump(out_data, open(output_file, 'wb'))


def load_circuit(name: str, type: str) -> Circuit:
    save_dir = "partitioned_circuits"
    output_file = f"out_circuits_pam_3_synth_4/{type}/{name}.pkl"
    block_3_circuit = pickle.load(
        open(
            f"{save_dir}/block_3/bqskit_{type}_{name}.pkl",
            'rb',
        )
    )
    circuit: Circuit = block_3_circuit

    num_3q_blocks = sum(1 for op in circuit.operations() if isinstance(op.gate, CircuitGate))
    circuit.unfold_all()

    return circuit, num_3q_blocks, output_file

def load_machine_model(circ: Circuit, layout: str = "None") -> MachineModel:
    return MachineModel(circ.num_qudits)

if __name__ == "__main__":
    circuit_name = sys.argv[1]
    type = sys.argv[2]  # 'hamlib' 'qasm_bench' or 'feynman'

    assert type in ['hamlib', 'qasm_bench', 'feynman']

    circ, num_3q_blocks, output_file = load_circuit(circuit_name,  type)

    model = load_machine_model(circ=circ)

    launch_circ(circ, model, num_3q_blocks, output_file)


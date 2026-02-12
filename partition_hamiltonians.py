"""Generate all Hamiltonian circuits, compile them, and save them to a directory"""
from bqskit import compile
from bqskit.compiler import Compiler
from pathlib import Path
import pickle

from benchpress.bqskit_gym.utils.bqskit_backend_utils import BqskitFlexibleBackend
from benchpress.utilities.io import input_circuit_properties, output_circuit_properties, output_bqskit_circuit
from benchpress.utilities.io.hamiltonians import generate_hamiltonian_circuit
from benchpress.workouts.validation import benchpress_test_validation
from benchpress.config import Configuration
from benchpress.utilities.validation import circuit_validator

from bqskit.ir import Circuit
from sys import argv

from bqskit.passes.partitioning import QuickPartitioner

from benchpress.workouts.abstract_transpile.hamlib_hamiltonians import (
    HAM_TOPO,
    HAM_TOPO_NAMES,
)

if __name__ == '__main__':
    # Loop through all HAM_TOPOs and run bqskit compile on them
    compiler = Compiler(num_workers=-1)
    block_size = int(argv[1]) if len(argv) > 1 else 3
    workflow = [
        QuickPartitioner(block_size),
    ]

    all_ids = []
    save_dir = "partitioned_circuits"

    for ham_top, name in zip(HAM_TOPO, HAM_TOPO_NAMES):
        print(f'Running {name}')
        save_file = Path(save_dir) / f"block_{block_size}" / f'bqskit_hamlib_{name}.pkl'
        if save_file.exists():
            print(f'Skipping {name}, already exists at {save_file}')
            continue
        circuit, qasm = generate_hamiltonian_circuit(
            ham_top[0].pop("ham_hamlib_hamiltonian"), None
        )

        out_id = compiler.submit(
            circuit=circuit,
            workflow=workflow,
        )

        all_ids.append((out_id, ham_top[1], name))
        num_qudits = circuit.num_qudits
        gates = circuit.gate_counts


    for out_id, topo_name, name in all_ids:
        result: Circuit = compiler.result(out_id)
        print(f'Finished {name}')
        print(result.gate_counts)
        save_file = Path(save_dir) / f"block_{block_size}" / f'bqskit_hamlib_{name}.pkl'
        save_file.parent.mkdir(parents=True, exist_ok=True)
        pickle.dump(result, open(save_file, 'wb'))
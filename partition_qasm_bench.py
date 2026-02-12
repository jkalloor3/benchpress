"""Generate all QASMBench circuits, compile them, and save them to a directory"""
from pathlib import Path
import pickle
from sys import argv
from bqskit import compile
from bqskit.ir import Circuit
from bqskit.compiler import Compiler
from benchpress.utilities.io import qasm_circuit_loader

from bqskit.passes.partitioning import QuickPartitioner

from benchpress.workouts.abstract_transpile.qasmbench import (
    SMALL_CIRC_TOPO,
    SMALL_NAMES,
    MEDIUM_CIRC_TOPO,
    MEDIUM_NAMES,
    LARGE_CIRC_TOPO,
    LARGE_NAMES,
)

if __name__ == '__main__':
    # Loop through all QASMBench circuits and run bqskit compile on them
    compiler = Compiler(num_workers=-1)
    block_size = int(argv[1]) if len(argv) > 1 else 3
    size = int(argv[2]) if len(argv) > 2 else 2
    workflow = [
        QuickPartitioner(block_size),
    ]

    all_ids = []
    save_dir = "partitioned_circuits"

    # Split into SMALL, MEDIUM, LARGE based on qubit count

    if size == 2:
        data = zip(SMALL_CIRC_TOPO, SMALL_NAMES)
    elif size == 1:
        data = zip(MEDIUM_CIRC_TOPO, MEDIUM_NAMES)
    else:
        data = zip(LARGE_CIRC_TOPO, LARGE_NAMES)

    for circ_and_topo, name in data:
        print(f'Running {name}')
        save_file = Path(save_dir) / f"block_{block_size}" / f'bqskit_qasm_bench_{name}.pkl'
        if save_file.exists():
            print(f'Skipping {name}, already exists at {save_file}')
            continue
        try:
            circuit = qasm_circuit_loader(circ_and_topo[0], None)
        except Exception as e:
            print(f'Failed to load {name} from {circ_and_topo[0]}: {e}')
            continue

        out_id = compiler.submit(
            circuit=circuit,
            workflow=workflow,
        )

        all_ids.append((out_id, name))

    for out_id, name in all_ids:
        result: Circuit = compiler.result(out_id)
        print(f'Finished {name}')
        print(result.gate_counts)
        save_file = Path(save_dir) / f"block_{block_size}" / f'bqskit_qasm_bench_{name}.pkl'
        save_file.parent.mkdir(parents=True, exist_ok=True)
        pickle.dump(result, open(save_file, 'wb'))
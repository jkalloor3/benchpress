"""Generate all Feynman circuits and save them to a QASM directory"""
import os
import pickle
import shutil
from sys import argv
from pathlib import Path
from bqskit import compile
from bqskit.compiler import Compiler

from benchpress.utilities.io import qasm_circuit_loader, output_circuit_properties
from benchpress.config import Configuration

from bqskit.ir.circuit import Circuit
from bqskit.passes.partitioning import QuickPartitioner

if __name__ == '__main__':
    compiler = Compiler(num_workers=-1)
    block_size = int(argv[1]) if len(argv) > 1 else 3
    workflow = [
        QuickPartitioner(block_size),
    ]

    feynman_dir = Configuration.get_qasm_dir("feynman")
    print(f'Loading circuits from {feynman_dir}')

    file_names = [x for x in os.listdir(feynman_dir) if x.endswith(".qasm")]
    names = [x.replace('.qasm', '') for x in file_names]

    all_ids = []
    save_dir = "partitioned_circuits"

    for file_name, name in zip(file_names, names):
        print(f'Running {name}')
        try:
            circuit = qasm_circuit_loader(f"{feynman_dir}{file_name}")
        except Exception as e:
            print(f'Failed to load {name} from {feynman_dir}{file_name}: {e}')
            continue

        num_qudits = circuit.num_qudits

        # Copy qasm file to new file name
        circ_type = "feynman"
        new_circ_name = f'{name}_{num_qudits}q'

        qasm_file = f'qasm_files/{circ_type}/{new_circ_name}.qasm'
        Path(qasm_file).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f"{feynman_dir}{file_name}", qasm_file)
        print(f'Copied QASM to {qasm_file}')

        # out_id = compiler.submit(
        #     circuit=circuit,
        #     workflow=workflow,
        # )

        # all_ids.append((out_id, name))

    # for out_id, name in all_ids:
    #     result: Circuit = compiler.result(out_id)
    #     print(f'Finished {name}')
    #     # print(result.gate_counts)
    #     save_file = Path(save_dir) / f"block_{block_size}" / f'bqskit_feynman_{name}.pkl'
    #     save_file.parent.mkdir(parents=True, exist_ok=True)
    #     pickle.dump(result, open(save_file, 'wb'))
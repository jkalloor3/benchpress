import time
import os
import subprocess
import glob
from pathlib import Path
import pickle
from bqskit.ir.circuit import Circuit

sleep_time = 0.05
file_name = 'job.sh'

header = """#!/bin/bash -l
#SBATCH -q regular
#SBATCH -A m4141
#SBATCH -C cpu
#SBATCH --time={time_str}
#SBATCH -N 1
#SBATCH --signal=B:USR1@1
#SBATCH --output=./slurm_logs/{circ_type}/{circ}.log

module load conda
conda activate /pscratch/sd/j/jkalloor/benchpress_env
echo "python {file}.py {circ} {circ_type}"
python {file}.py {circ} {circ_type}
"""


circ_types = ['hamlib', 'qasm_bench', 'feynman']

time_strs = [
    "03:00:00",  
    "06:00:00",
    "11:55:00"
]

save_dir = "partitioned_circuits"

if __name__ == '__main__':
    file = "run_circ"

    slurm_log_form = "slurm_logs/{circ_type}/{circ}.log"
    output_file_form = "out_circuits_pam_3_synth_4/{circ_type}/{circ}.pkl"


    trial_circ_type = "qasm_bench"

    circ_files = glob.glob(os.path.join(save_dir, "block_3", f"*{trial_circ_type}*.pkl"))

    # Get all circuit names
    circ_names = [Path(f).stem.split("bqskit_")[1] for f in circ_files]

    extremely_big_circuits = []

    for circ in circ_names:
        # Get circuit type
        if 'hamlib' in circ:
            circ_type = 'hamlib'
        elif 'qasm_bench' in circ:
            circ_type = 'qasm_bench'
        elif 'feynman' in circ:
            circ_type = 'feynman'

        circ_name = circ.replace(f"{circ_type}_", "")

        # Check if ran by seeing if slurm log exists
        has_run = os.path.exists(
            slurm_log_form.format(circ_type=circ_type, circ=circ_name)
        )
        # Check if output file exists
        has_output = os.path.exists(
            output_file_form.format(circ_type=circ_type, circ=circ_name)
        )

        if not has_run:
            continue  # Hasn't run yet, so skip

        if has_output:
            print(f"Skipping {circ} as output exists.")
        

        # Read the number of qudits from the file
        block_3_circuit: Circuit = pickle.load(
            open(
                f"{save_dir}/block_3/bqskit_{circ_type}_{circ_name}.pkl",
                'rb',
            )
        )

        num_qudits = block_3_circuit.num_qudits

        if num_qudits <= 20:
            time_str = time_strs[0]
        elif num_qudits <= 40:
            time_str = time_strs[1]
        else:
            time_str = time_strs[2]


        # if has_run and not has_output:
        print(f"Circuit {circ} has run but has no output. Originally submitted with time {time_str}. Resubmitting.")


        if num_qudits > 40:
            print(f"Skipping {circ} as it will not run in 12 hours. Adding to multi-node resubmission queue.")
            extremely_big_circuits.append(circ)
            continue


        time_str = time_strs[2]  # Give max time for resubmission

        to_write = open(file_name, 'w')
        to_write.write(header.format(file=file, circ=circ_name, circ_type=circ_type,
                                     time_str=time_str))
        to_write.close()
        time.sleep(2*sleep_time)
        print(f"python {file}.py {circ} {circ_type}")
        output = subprocess.check_output(['sbatch' , file_name])
        print(output)


    print("Extremely big circuits to be resubmitted with multi-node:")
    print(extremely_big_circuits)

    pickle.dump(
        extremely_big_circuits,
        open(f'extremely_big_circuits_resubmit_{trial_circ_type}.pkl', 'wb')   
    )
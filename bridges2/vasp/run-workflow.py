import os
import subprocess
from pathlib import Path

import yaml
from atomate2.settings import Atomate2Settings
from jobflow import run_locally
from mp_api.client import MPRester
from pymatgen.io.vasp.sets import MPStaticSet

resources = {
    "job_name": "benchmark",
    "nodes": os.environ.get("SLURM_JOB_NUM_NODES"),
    "ntasks_per_node": os.environ.get("SLURM_NTASKS_PER_NODE", 64),
    "time": "00:30:00",
    "constraint": "cpu",
    "partition": "RM",
    # "qverbatim": "#SBATCH --gpu-bind=none\n#SBATCH --gpus=4"
    # if constraint == "gpu"
    # else "",
}
ntasks = int(resources["nodes"]) * int(resources["ntasks_per_node"])

atomate2_config_file = Path(
    f"~/atomate2/config/atomate2-{resources['job_name']}-{resources['nodes']}-{resources['ntasks_per_node']}.yaml"
).expanduser()

with open(atomate2_config_file, "w") as f:
    yaml.dump(
        {
            "VASP_CMD": f"mpirun -np {ntasks} /opt/packages/VASP/VASP6/6.4.3/GNU-SHMEM/vasp_std",
            "VASP_GAMMA_CMD": f"mpirun -np {ntasks} /opt/packages/VASP/VASP6/6.4.3/GNU-SHMEM/vasp_gam",
        },
        f,
    )

settings = Atomate2Settings(
    CONFIG_FILE=str(atomate2_config_file),
    VASP_CMD=f"mpirun -np {ntasks} /opt/packages/VASP/VASP6/6.4.3/GNU-SHMEM/vasp_std",
)
print(settings.CONFIG_FILE)
print(settings.VASP_CMD)


os.environ["ATOMATE2_CONFIG_FILE"] = str(atomate2_config_file)

subprocess.run("echo $ATOMATE2_CONFIG_FILE", shell=True)

subprocess.run(f"export ATOMATE2_CONFIG_FILE={atomate2_config_file}", shell=True)
subprocess.run(
    "module load openmpi/5.0.3-gcc13.2.1 intel-mkl/2023.2.0 cuda/11.7.1", shell=True
)
subprocess.run(
    "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/packages/hdf5/hdf5-1.14.5/GNU/lib",
    shell=True,
)


with MPRester() as mpr:
    docs = mpr.materials.summary.search(
        chemsys=["Pb-Ti-O", "Pb-Zr-O", "Pb-Ti-Zr-O"],
        spacegroup_symbol="Pm-3m",  # "P4mm" "R3mm"
        fields=["material_id", "symmetry", "structure"],
    )

structure = docs[0].structure

from atomate2.vasp.jobs.core import StaticMaker

# create a custom input generator set with a larger ENCUT
input_set_generator = MPStaticSet(
    user_incar_settings={
        "EDIFF": 1e-5,
        "LCALCPOL": True,
        "LCALCEPS": True,
        "IBRION": 5,
        "ISMEAR": 0,
        # "ENCUT": 800
    }
)

# initialise the static maker to use the custom input set generator
static_maker = StaticMaker(
    input_set_generator=input_set_generator,
    run_vasp_kwargs=dict(
        vasp_cmd=settings.VASP_CMD,
        vasp_gamma_cmd=settings.VASP_GAMMA_CMD,
    ),
)

# create a job using the customised maker
flow = static_maker.make(structure)


print("Running workflow")


run_locally(flow, create_folders=True)

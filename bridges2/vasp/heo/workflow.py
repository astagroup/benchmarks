# %%
import argparse
import logging
import os
from pathlib import Path

import yaml
from atomate2.settings import Atomate2Settings
from atomate2.vasp.jobs.core import StaticMaker
from atomate2.vasp.powerups import add_metadata_to_flow
from jobflow import run_locally
from pymatgen.core import Structure
from pymatgen.io.vasp.sets import MPStaticSet

# retrieve a structure from the MP database (demo, not used in workflow)
# from mp_api.client import MPRester

# with MPRester() as mpr:
#     docs = mpr.materials.summary.search(
#         chemsys=["Pb-Ti-O", "Pb-Zr-O", "Pb-Ti-Zr-O"],
#         spacegroup_symbol="P4mm", #"Pm-3m", "P4mm" "R3mm"
#         fields=["material_id", "symmetry", "structure"],
#     )

# structure = docs[1].structure * (3, 3, 2)
# structure.to(filename=f"POSCAR.{structure.to_ase_atoms().get_chemical_formula()
# }")

# %% General, HPC resources, atomate2 settings

__version__ = "0.0.1"
ncpus_per_node = 64


# Run setup.sh instead

# os.environ["ATOMATE2_CONFIG_FILE"] = str(atomate2_config_file)
# subprocess.run("echo $ATOMATE2_CONFIG_FILE", shell=True)
# subprocess.run(f"export ATOMATE2_CONFIG_FILE={atomate2_config_file}", shell=True)
# subprocess.run(
#     "module load openmpi/5.0.3-gcc13.2.1 intel-mkl/2023.2.0 cuda/11.7.1", shell=True
# )
# subprocess.run(
#     "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/packages/hdf5/hdf5-1.14.5/GNU/lib",
#     shell=True,
# )


# %% Utility functions
def run_vasp_job(
    structure: Structure,
    resources: dict,
    settings: Atomate2Settings,
    user_incar_settings: dict,
    version: str,
):
    logging.info("Running atomate2 VASP job")

    # create a custom input generator set with a larger ENCUT
    input_set_generator = MPStaticSet(
        user_incar_settings=user_incar_settings,
        reciprocal_density=200,
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

    add_metadata_to_flow(
        flow,
        additional_fields={
            "project": resources["job_name"],
            "resources": resources,
            "version": version,
        },
    )

    run_locally(flow, create_folders=False)


# %% Run benchmark


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "config", type=str, help="Path to the configuration yaml file"
    )
    args = argparser.parse_args()

    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    vasp_path = config["job"]["vasp"]["path"]
    resources = config["scheduler"]["resources"]

    nodes = int(resources["nodes"] or os.environ.get("SLURM_JOB_NUM_NODES", 1))
    ntasks_per_node = int(
        resources["ntasks_per_node"]
        or os.environ.get("SLURM_NTASKS_PER_NODE", ncpus_per_node)
    )
    num_processes = nodes * ntasks_per_node

    structure = Structure.from_file(Path(__file__).parent / "POSCAR.O108Pb36Ti18Zr18")

    user_incar_settings = {
        "ALGO": "Normal",
        "EDIFF": 1e-4,
        "ENCUT": 800,
        "ISMEAR": 0,
        "LREAL": "Auto",
    }

    user_incar_settings.update(config["job"]["vasp"]["INCAR"])

    atomate2_config_file = Path(
        f"~/atomate2/config/atomate2-{resources['job_name']}-{resources['nodes']}-{resources['ntasks_per_node']}.yaml"
    ).expanduser()
    atomate2_config_file.parent.mkdir(parents=True, exist_ok=True)

    with open(atomate2_config_file, "w") as f:
        yaml.dump(
            {
                "VASP_CMD": f"mpirun -np {num_processes} {vasp_path}/vasp_std",
                "VASP_GAMMA_CMD": f"mpirun -np {num_processes} {vasp_path}/vasp_gam",
            },
            f,
        )

    settings = Atomate2Settings(
        CONFIG_FILE=str(atomate2_config_file),
        VASP_CMD=f"mpirun -np {num_processes} {vasp_path}/vasp_std",
        VASP_GAMMA_CMD=f"mpirun -np {num_processes} {vasp_path}/vasp_gam",
    )

    run_vasp_job(
        structure=structure,
        resources=resources,
        settings=settings,
        user_incar_settings=user_incar_settings,
        version=__version__,
    )


if __name__ == "__main__":
    main()

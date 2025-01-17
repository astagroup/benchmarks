#!/bin/bash

# Set the stack size to unlimited
ulimit -s unlimited

# Set the number of OpenMP threads
export OMP_NUM_THREADS=1

# Load required modules
module purge
module load anaconda3
source activate comm
module load openmpi/5.0.3-gcc13.2.1 intel-mkl/2023.2.0 cuda/11.7.1

# Uncomment the following lines if these modules are required for your workflow
# module load intel-compiler intel-icc intel-mpi intel-mkl
# module load VASP/6.4.3-intel

# Update the library path to include custom HDF5 library path
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/packages/hdf5/hdf5-1.14.5/GNU/lib

#!/bin/bash

module purge

ulimit -s unlimited
export OMP_NUM_THREADS=1

module load openmpi/5.0.3-gcc13.2.1 intel-mkl/2023.2.0 cuda/11.7.1
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/packages/hdf5/hdf5-1.14.5/GNU/lib

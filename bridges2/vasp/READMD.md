

VAPS manual has [recommended procedures](https://www.vasp.at/wiki/index.php/Optimizing_the_parallelization) to optimize parallization. Some considerations included during this test are:


1. According to VASP NCORE manual: 

    > NCORE is available from VASP.5.2.13 on, and is more handy than the previous parameter NPAR. The user should either specify NCORE or NPAR, where NPAR takes a higher preference. The relation between both parameters is
    > `NCORE =number-of-cores /KPAR / NPAR`

    Therefore we consider only `NCORE` and `KPAR` but not `NPAR`

1. Choose `NCORE` as a factor of the cores per node. As Bridge2 has 64 CPUs per CPU node. Here I consider `NCORE=1,2,4,8,16,32,64`, assuming we always request and use all CPUs. 

1. `KPAR` should be set KPAR up to the number of irreducible k points and should be an integer divisor of the total number of core. Here I consider `KPAR=1,2,4,8,16,32,64<=KPOINTS`. In the case of ZrTi(PbO3)2 of 180 atoms, the number of kpoints is only 2x2x4=16 (reciprocal density of ~200).

1. Enumerate all the allowed combinations of `NCORE` and `KPAR`, and test on 1,2,4,16 nodes.




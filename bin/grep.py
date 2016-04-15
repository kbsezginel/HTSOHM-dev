#! /usr/bin/env python

def grep(run_ID, mat_ID):

    import os
    import subprocess
    import shlex
    import shutil
    ML_data = "Output/System_0/output_%s-%s_1.1.1_298.000000_3.5e+06.data" % (run_ID, mat_ID)
    with open(ML_data) as origin:
        for line in origin:
            if "absolute [mol/kg" in line:
                ML_a_mk = line.split()[5]
            elif "absolute [cm^3 (STP)/g" in line:
                ML_a_cg = line.split()[6]
            elif "absolute [cm^3 (STP)/c" in line:
                ML_a_cc = line.split()[6]
            elif "excess [mol/kg" in line:
                ML_e_mk = line.split()[5]
            elif "excess [cm^3 (STP)/g" in line:
                ML_e_cg = line.split()[6]
            elif "excess [cm^3 (STP)/c" in line:
                ML_e_cc = line.split()[6]

    print( "\nMETHANE LOADING\tabsolute\texcess\n" +
           "mol/kg\t\t%s\t%s\n" % (ML_a_mk, ML_e_mk) +
           "cc/g\t\t%s\t%s\n" % (ML_a_cg, ML_e_cg) +
           "cc/cc\t\t%s\t%s\n" % (ML_a_cc, ML_e_cc) )

if __name__ == "__main__":
    import sys
    grep(str(sys.argv[1]),
         int(sys.argv[2]))

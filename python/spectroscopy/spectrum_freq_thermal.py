#!/usr/local/bin/python3

"""
 Compute a black body spectrum at requested temperature
 SI units of B_nu versus frequency

   Usage: spectrum_thermal.py temperature  outfile.dat
   Input: temperature [K]
   Output: radiance [watt/steradian /meter^2 /Hz]
   Exitance: multiply by pi for exitance  [watt /meter^2 /Hz]

"""

import os
import sys
import numpy as np
import math as ma


if len(sys.argv) == 3:
  temperature = float(sys.argv[1])
  outfile = sys.argv[2]
else:
  print(" Compute the blackbody radiance at requested temperature\n")
  print("   Usage: spectrum_freq_thermal.py temperature  outfile.dat ")
  print("   Input: temperature [K]")
  print("   Output: radiance [watt/steradian /meter^2 /Hz]")
  print("   Exitance: multiply by pi for exitance  [watt /meter^2 /Hz]")
  print(" ")
  sys.exit(" ")

print(" Blackbody spectrum at ", temperature, " K")
  
numin = 1.e9
numax = 5.e14
nnus = 4096
hplanck = 6.62607004e-34
clight = 299792458.
kboltzmann = 1.38064852e-23

dnu = (numax - numin) / float(nnus)

freq = [0.] * (nnus)
flux = [0.] * (nnus)

for i in range (nnus):
  nu = numin + dnu * i
  bnu = (2.*hplanck*nu*nu*nu/(clight*clight))/(ma.exp(hplanck*nu/(kboltzmann*temperature)) - 1.)
  freq[i] = nu
  flux[i] = bnu


outdata = np.column_stack((freq,flux))
np.savetxt(outfile, outdata)

exit()

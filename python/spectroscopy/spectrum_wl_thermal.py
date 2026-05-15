#!/usr/local/bin/python3

"""
 Compute a black body spectrum at requested temperature
 SI units of B_lambda versus wavelength
 

   Usage: spectrum_wl_thermal.py temperature  outfile.dat
   Input: temperature [K]
   Output: radiance [watt/steradian /meter^2 /micron]
   Exitance: multiply by pi for exitance  [watt /meter^2 /micron]

"""

import os
import sys
import numpy as np
import math as ma


if len(sys.argv) == 3:
  temperature = float(sys.argv[1])
  outfile = sys.argv[2]
else:
  print(" Compute blackbody radiance at requested temperature\n")
  print("   Usage: spectrum_wl_thermal.py temperature  outfile.dat ")
  print("   Input: temperature [K]")
  print("   Output: radiance [watt/steradian /meter^2 /micron]")
  print("   Exitance: multiply by pi for exitance  [watt /meter^2 /micron]")
  print(" ")
  sys.exit(" ")

print(" Blackbody spectrum at ", temperature, " K")
  
numin = 1.e9
numax = 5.e14
nnus = 4096
hplanck = 6.62607004e-34
clight = 299792458.
kboltzmann = 1.38064852e-23

# Calculate the radiance in frequency units and then convert to per micron

dnu = (numax - numin) / float(nnus)

freq = [0.] * (nnus)
flux = [0.] * (nnus)

for i in range (nnus):
  nu = numin + dnu * i
  bnu = (2.*hplanck*nu*nu*nu/(clight*clight))/(ma.exp(hplanck*nu/(kboltzmann*temperature)) - 1.)
  # Convert frequency to wavelength and save this step
  freq[i] = 1.0e6*clight/nu
  # Convert radiance to per meter (SI units) by multiplying dnu/dlambda = nu/lambda
  # Convert per meter to per micron (10^-6 m)
  flux[i] = 1.0e-6*bnu*nu/(clight/nu)


outdata = np.column_stack((freq,flux))
np.savetxt(outfile, outdata)

exit()
